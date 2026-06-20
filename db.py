import os
import json
import datetime
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_ID   = os.environ.get("SHEET_ID", "")
CREDS_JSON = os.environ.get("GOOGLE_CREDS", "")

def _client():
    info  = json.loads(CREDS_JSON)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)

def _ws(tab):
    return _client().open_by_key(SHEET_ID).worksheet(tab)

def _all(tab):
    try:
        records = _ws(tab).get_all_records()
        return records if records else []
    except Exception as e:
        print(f"[DB] data evaluation conflict on {tab}: {e}")
        return []

def _add(tab, row: dict):
    try:
        ws      = _ws(tab)
        headers = ws.row_values(1)
        ws.append_row([str(row.get(h, "")) for h in headers])
        return True
    except Exception as e:
        print(f"[DB] transactional record fault on {tab}: {e}")
        return False

def _upd(tab, col, val, data: dict):
    try:
        ws      = _ws(tab)
        headers = ws.row_values(1)
        cidx    = headers.index(col) + 1
        cell    = ws.find(str(val), in_column=cidx)
        if not cell: return False
        for k, v in data.items():
            if k in headers:
                ridx = headers.index(k) + 1
                ws.update_cell(cell.row, ridx, str(v))
        return True
    except Exception as e:
        print(f"[DB] record write execution block on {tab}: {e}")
        return False

def _del2(tab, col1, val1, col2, val2):
    try:
        ws      = _ws(tab)
        headers = ws.row_values(1)
        c1      = headers.index(col1) + 1
        c2      = headers.index(col2) + 1
        cells   = ws.findall(str(val1), in_column=c1)
        for row in reversed([c.row for c in cells]):
            if str(ws.cell(row, c2).value) == str(val2):
                ws.delete_rows(row)
    except Exception as e:
        print(f"[DB] structural deletion row tracking index failure {tab}: {e}")

def register_user(uid, username, fullname):
    users = _all("users")
    if any(str(u.get("id")) == str(uid) for u in users):
        return
    _add("users", {"id": str(uid), "username": username, "fullname": fullname, "lang": "en", "is_banned": "false"})

def get_lang(uid):
    for u in _all("users"):
        if str(u.get("id")) == str(uid):
            return u.get("lang", "en")
    return "en"

def set_lang(uid, lng):
    _upd("users", "id", uid, {"lang": lng})

def is_banned(uid):
    for u in _all("users"):
        if str(u.get("id")) == str(uid):
            return str(u.get("is_banned", "false")).lower() == "true"
    return False

def ban_user(uid):
    _upd("users", "id", uid, {"is_banned": "true"})

def unban_user(uid):
    _upd("users", "id", uid, {"is_banned": "false"})

def get_maintenance():
    config = _all("config")
    if config:
        return str(config[0].get("maintenance_mode", "false")).lower() == "true"
    return False

def set_maintenance(flag: bool):
    """FIXED: If the system row doesn't exist to update, it will automatically create it."""
    val = "true" if flag else "false"
    if not _upd("config", "id", "system", {"maintenance_mode": val}):
        _add("config", {"id": "system", "maintenance_mode": val})

def get_all_users():
    return _all("users")

def stats():
    users = _all("users")
    jobs = _all("jobs")
    subs = _all("subscriptions")
    return len(users), sum(1 for u in users if str(u.get("is_banned", "false")).lower() == "true"), len(jobs), len(subs)

def all_categories():
    """FIXED: Now accurately filters so it only displays categories that actually have active jobs."""
    cats = set()
    for j in _all("jobs"):
        if j.get("category") and str(j.get("is_active", "false")).lower() == "true":
            cats.add(str(j["category"]))
    return sorted(list(cats))

def jobs_by_category(cat):
    return [j for j in _all("jobs") if str(j.get("category")) == cat and str(j.get("is_active", "false")).lower() == "true"]

def search_jobs(q):
    """UPDATED: Now indexes new job metrics seamlessly to optimize user matching strings."""
    q = q.lower()
    res = []
    for j in _all("jobs"):
        if str(j.get("is_active", "false")).lower() != "true": continue
        if (q in str(j.get("title", "")).lower() or 
            q in str(j.get("description", "")).lower() or
            q in str(j.get("education_level", "")).lower() or
            q in str(j.get("language", "")).lower() or
            q in str(j.get("experience", "")).lower()):
            res.append(j)
    return res

def save_job(job_data):
    """FIXED: Included the missing save_job function for your Google Sheets setup."""
    if "is_active" not in job_data:
        job_data["is_active"] = "true"
    return _add("jobs", job_data)

def record_apply(uid, jid):
    _add("tracked_applications", {"user_id": str(uid), "job_id": str(jid), "timestamp": str(datetime.datetime.now())})

def add_subscription(uid, cat):
    subs = _all("subscriptions")
    if any(str(s.get("user_id")) == str(uid) and str(s.get("category")) == str(cat) for s in subs):
        return False
    return _add("subscriptions", {"user_id": str(uid), "category": str(cat)})

def user_subscriptions(uid):
    return [str(s.get("category")) for s in _all("subscriptions") if str(s.get("user_id")) == str(uid)]

def add_keyword(uid, kw):
    kws = _all("keyword_alerts")
    kw = kw.strip().lower()
    if any(str(k.get("user_id")) == str(uid) and str(k.get("keyword")) == kw for k in kws):
        return False
    return _add("keyword_alerts", {"user_id": str(uid), "keyword": kw})

def user_keywords(uid):
    return [str(k.get("keyword", "")) for k in _all("keyword_alerts") if str(k.get("user_id")) == str(uid)]

def remove_keyword(uid, kw):
    _del2("keyword_alerts", "user_id", str(uid), "keyword", str(kw).strip().lower())

def save_cv(uid, data):
    cvs = _all("user_cvs")
    exists = any(str(c.get("user_id")) == str(uid) for c in cvs)
    clean = {k: str(v)[:500] for k, v in data.items() if v}
    clean["user_id"] = str(uid)
    if exists:
        _upd("user_cvs", "user_id", str(uid), clean)
    else:
        _add("user_cvs", clean)

def get_cv(uid):
    for c in _all("user_cvs"):
        if str(c.get("user_id")) == str(uid):
            return c
    return None

def is_notified(uid, jid):
    logs = _all("notification_logs")
    return any(str(l.get("user_id")) == str(uid) and str(l.get("job_id")) == str(jid) for l in logs)

def mark_notified(uid, jid):
    _add("notification_logs", {"user_id": str(uid), "job_id": str(jid), "sent_at": str(datetime.datetime.now())})
