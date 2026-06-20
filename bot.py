import keep_alive
keep_alive.start()

import os
import asyncio
import datetime
import urllib.parse
import telegram.error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, filters)
import db
from language import t
from cv_matcher import match_jobs
from online_work import get_category

TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "0").split(",")))
BOT_USERNAME = "MuyaSeekerbot"
YOUTUBE_GUIDE_URL = "https://youtu.be/WG3c9GJWhRE"

CV_FIELDS    = ["full_name","email","phone","location","summary",
                "education","experience","skills","languages"]
CV_QUESTIONS = ["cv_q1","cv_q2","cv_q3","cv_q4","cv_q5",
                "cv_q6","cv_q7","cv_q8","cv_q9"]

def _b(label, cb):  return InlineKeyboardButton(label, callback_data=cb)
def _url(label, u): return InlineKeyboardButton(label, url=u)
def _back(cb, lng): return _b(t(lng, "back"), cb)

def _fmt_job(j, lng):
    """Formats and displays structural job requirement fields."""
    today = str(datetime.date.today())
    status = t(lng, "open") if str(j.get("deadline", "")) >= today else t(lng, "closed")
    
    lbl_edu  = "🎓 *Education Level:* " if lng == "en" else "🎓 *የትምህርት ደረጃ:* "
    lbl_lang = "🌐 *Language:* "         if lng == "en" else "🌐 *አስፈላጊ ቋንቋ:* "
    lbl_exp  = "💼 *Experience:* "        if lng == "en" else "💼 *የስራ ልምድ:* "
    lbl_vac  = "👥 *Vacancies:* "         if lng == "en" else "👥 *ክፍት ቦታ ብዛት:* "
    lbl_gen  = "⚥ *Gender:* "             if lng == "en" else "⚥ *ጾታ:* "
    
    return (
        f"📋 *{j.get('title','N/A')}*\n\n"
        f"🏢 *Company:* {j.get('company','N/A')}\n"
        f"📍 *Location:* {j.get('location','N/A')}\n"
        f"📂 *Category:* {j.get('category','N/A')}\n"
        f"⏳ *Deadline:* {j.get('deadline','N/A')} ({status})\n\n"
        f"✨ *Requirements:*\n"
        f"{lbl_edu}{j.get('education_level', 'N/A')}\n"
        f"{lbl_lang}{j.get('language', 'N/A')}\n"
        f"{lbl_exp}{j.get('experience', 'N/A')}\n"
        f"{lbl_vac}{j.get('required_people', 'N/A')}\n"
        f"{lbl_gen}{j.get('gender', 'N/A')}\n\n"
        f"📝 *Description:* {j.get('description','No details specified.')}\n\n"
        f"🌐 *Source:* {j.get('source','N/A')}"
    )

def _job_keyboard(j, lng, back_cb="main_menu"):
    url = str(j.get("apply_url", "#"))
    return InlineKeyboardMarkup([
        [_url(t(lng, "apply"), url)],
        [_b(t(lng, "track"), f"track:{j.get('id')}")],
        [_back(back_cb, lng)]
    ])

async def _send_msg(upd: Update, ctx, text: str, reply_markup=None, edit=False):
    """Delivers text instantly without delays or typing animations."""
    chat_id = upd.effective_chat.id
    try:
        if edit and upd.callback_query:
            await upd.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await ctx.bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception:
        pass

async def _guard(upd: Update, ctx):
    u = upd.effective_user
    if not u: return False
    if db.is_banned(u.id):
        if upd.message:
            await _send_msg(upd, ctx, "🚫 Access Denied: Account Restrained.", edit=False)
        elif upd.callback_query:
            await upd.callback_query.answer("🚫 Account restricted by administration.", show_alert=True)
        return False
    if db.get_maintenance() and u.id not in ADMIN_IDS:
        m_msg = "🔧 MuyaSeekerbot is currently undergoing system optimization. Please return later."
        if upd.message:
            await _send_msg(upd, ctx, m_msg, edit=False)
        elif upd.callback_query:
            await _send_msg(upd, ctx, m_msg, edit=True)
        return False
    return True

async def start(upd: Update, ctx):
  
    try:
        await ctx.bot.send_chat_action(chat_id=upd.effective_user.id, action=ChatAction.TYPING)
    except Exception:
        pass

    uid = upd.effective_user.id
    db.register_user(uid, upd.effective_user.username or "", upd.effective_user.full_name or "")
    if not await _guard(upd, ctx): return
    kbd = InlineKeyboardMarkup([
        [_b("English", "set_lang:en"), _b("አማርኛ", "set_lang:am")]
    ])
    await _send_msg(upd, ctx, t("en", "welcome"), reply_markup=kbd, edit=False)

async def show_main(upd: Update, ctx, lng):
    kbd = InlineKeyboardMarkup([
        [_b(t(lng, "browse"), "browse"), _b(t(lng, "search"), "search_prompt")],
        [_b(t(lng, "online"), "online_menu"), _b(t(lng, "alerts"), "alerts_menu")],
        [_b(t(lng, "mycv"), "cv_menu"), _b(t(lng, "lang"), "change_lang")]
    ])
    msg = t(lng, "main_menu")
    await _send_msg(upd, ctx, msg, reply_markup=kbd, edit=bool(upd.callback_query))

async def cmd_admin(upd: Update, ctx):
  
    try:
        await ctx.bot.send_chat_action(chat_id=upd.effective_user.id, action=ChatAction.TYPING)
    except Exception:
        pass

    if upd.effective_user.id not in ADMIN_IDS: return
    kbd = InlineKeyboardMarkup([
        [_b("📊 Operational Status", "adm:status"), _b("📢 Broadcast Global", "adm:bc_all")],
        [_b("🎯 Broadcast By ID", "adm:bc_select"), _b("🔑 Broadcast By Keyword", "adm:bc_kw")],
        [_b("🔧 Activate Maint Mode", "adm:m_on"), _b("✅ Resume Standard Ops", "adm:m_off")],
        [_b("🚫 Enforce Account Ban", "adm:ban_id"), _b("✅ Lift Account Restriction", "adm:unban_id")]
    ])
    await _send_msg(upd, ctx, "🛠 *MuyaSeeker Terminal*", reply_markup=kbd, edit=False)

async def cb_handler(upd: Update, ctx):
    try:
        await ctx.bot.send_chat_action(chat_id=upd.effective_user.id, action=ChatAction.TYPING)
    except Exception:
        pass

    q = upd.callback_query
    uid = q.from_user.id
    lng = db.get_lang(uid) or "en"
    
    await q.answer("⏳ Loading ..", show_alert=False)

    if q.data.startswith("adm:") and uid in ADMIN_IDS:
        action_flag = q.data.split(":", 1)[1]
        if action_flag == "status":
            u_c, b_c, j_c, s_c = db.stats()
            m_s = "ACTIVE ⚠️" if db.get_maintenance() else "INACTIVE ✅"
            status_text = (f"📊 *MuyaSeeker System Matrix Status*\n\n"
                           f"• Registered Node Entities: `{u_c}`\n"
                           f"• Restrained Core Channels: `{b_c}`\n"
                           f"• Database Job Postings: `{j_c}`\n"
                           f"• Active Subscriptions/Alerts: `{s_c}`\n"
                           f"• Global Maintenance Block: *{m_s}*")
            await _send_msg(upd, ctx, status_text, edit=False)
        elif action_flag == "bc_all":
            ctx.user_data["action"] = "broadcast"
            await _send_msg(upd, ctx, "📢 Supply text payload for global platform transmission:", edit=False)
        elif action_flag == "bc_select":
            ctx.user_data["action"] = "broadcast_selected"
            await _send_msg(upd, ctx, "🎯 Supply discrete payloads following layout format:\n`ID1,ID2 : Text message layout block here`", edit=False)
        elif action_flag == "bc_kw":
            ctx.user_data["action"] = "broadcast_keyword"
            await _send_msg(upd, ctx, "🔑 Supply keyword broadcast following layout format:\n`Keyword : Message text here`\n*(Example: python : We just posted a new Python job!)*", edit=False)
        elif action_flag == "ban_id":
            ctx.user_data["action"] = "ban"
            await _send_msg(upd, ctx, "🚫 Enter target structural Telegram ID numerical variable to restrict:", edit=False)
        elif action_flag == "unban_id":
            ctx.user_data["action"] = "unban"
            await _send_msg(upd, ctx, "✅ Enter target structural Telegram ID numerical variable to restore:", edit=False)
        elif action_flag == "m_on":
            db.set_maintenance(True)
            await _send_msg(upd, ctx, "🔧 Maintenance constraint arrays mapped *ON*.", edit=False)
        elif action_flag == "m_off":
            db.set_maintenance(False)
            await _send_msg(upd, ctx, "✅ Maintenance constraint arrays mapped *OFF*.", edit=False)
        return

    if not await _guard(upd, ctx): return

    if q.data.startswith("set_lang:"):
        new_lng = q.data.split(":")[1]
        db.set_lang(uid, new_lng)
        await show_main(upd, ctx, new_lng)
        
    elif q.data == "change_lang":
        kbd = InlineKeyboardMarkup([
            [_b("English", "set_lang:en"), _b("አማርኛ", "set_lang:am")],
            [_back("main_menu", lng)]
        ])
        await _send_msg(upd, ctx, "🌐 Choose Your Language / ቋንቋ ይምረጡ:", reply_markup=kbd, edit=True)
        
    elif q.data == "main_menu":
        ctx.user_data["action"] = None
        await show_main(upd, ctx, lng)
        
    elif q.data == "browse":
        cats = db.all_categories()
        if not cats:
            await _send_msg(upd, ctx, t(lng, "no_cats"), reply_markup=InlineKeyboardMarkup([[_back("main_menu", lng)]]), edit=True)
            return
        rows = [[_b(c, f"cat:{c}")] for c in cats]
        rows.append([_back("main_menu", lng)])
        await _send_msg(upd, ctx, t(lng, "cats_title"), reply_markup=InlineKeyboardMarkup(rows), edit=True)
        
    elif q.data.startswith("cat:"):
        cat_name = q.data.split(":", 1)[1]
        jobs = db.jobs_by_category(cat_name)
        if not jobs:
            await _send_msg(upd, ctx, t(lng, "no_jobs"), reply_markup=InlineKeyboardMarkup([[_back("browse", lng)]]), edit=True)
            return
        await q.message.delete()
        for j in jobs[:5]:
            await _send_msg(upd, ctx, _fmt_job(j, lng), reply_markup=_job_keyboard(j, lng, back_cb="browse"), edit=False)
        await _send_msg(upd, ctx, t(lng, "listings_end"), reply_markup=InlineKeyboardMarkup([[_back("browse", lng)]]), edit=False)
        
    elif q.data == "search_prompt":
        ctx.user_data["action"] = "search"
        await _send_msg(upd, ctx, t(lng, "search_prompt"), reply_markup=InlineKeyboardMarkup([[_back("main_menu", lng)]]), edit=True)
        
    elif q.data.startswith("track:"):
        jid = q.data.split(":")[1]
        db.record_apply(uid, jid)
        await q.answer(t(lng, "app_saved"))
        
    elif q.data == "online_menu":
        rows = [
            [_b(t(lng, "online_freelance"), "owi:freelance"), _b(t(lng, "online_remote"), "owi:remote")],
            [_b(t(lng, "online_airdrop"), "owi:airdrop"), _b(t(lng, "online_microtask"), "owi:microtask")],
            [_b(t(lng, "online_survey"), "owi:survey"), _b(t(lng, "online_youtube"), "owi:youtube")],
            [_b(t(lng, "video_guide"), "video_guide"), _b(t(lng, "share_bot"), "share_bot")],
            [_back("main_menu", lng)]
        ]
        await _send_msg(upd, ctx, t(lng, "online_title"), reply_markup=InlineKeyboardMarkup(rows), edit=True)
        
    elif q.data.startswith("owi:"):
        ckey = q.data.split(":")[1]
        cat = get_category(ckey)
        await q.message.delete()
        for i in cat.get("items", []):
            m = f"⭐ *{i['name']}*\n{i['desc']}\n\n_{i['tips']}_"
            kbd = InlineKeyboardMarkup([
                [_url(t(lng, "open_link"), i["url"])],
                [_back("online_menu", lng)]
            ])
            await _send_msg(upd, ctx, m, reply_markup=kbd, edit=False)
        await _send_msg(upd, ctx, t(lng, "listings_end"), reply_markup=InlineKeyboardMarkup([[_back("online_menu", lng)]]), edit=False)
        
    elif q.data == "alerts_menu":
        kbd = InlineKeyboardMarkup([
            [_b(t(lng, "sub_cat"), "sub_cats"), _b(t(lng, "add_kw"), "add_kw")],
            [_b(t(lng, "my_subs"), "my_subs"), _back("main_menu", lng)]
        ])
        await _send_msg(upd, ctx, t(lng, "alert_title"), reply_markup=kbd, edit=True)

    elif q.data == "sub_cats":
        cats = db.all_categories()
        rows = [[_b(c, f"sub:{c}")] for c in cats]
        rows.append([_back("alerts_menu", lng)])
        await _send_msg(upd, ctx, t(lng, "cats_title"), reply_markup=InlineKeyboardMarkup(rows), edit=True)
        
    elif q.data.startswith("sub:"):
        cat_name = q.data.split(":", 1)[1]
        if db.add_subscription(uid, cat_name):
            await _send_msg(upd, ctx, t(lng, "sub_saved", cat=cat_name), reply_markup=InlineKeyboardMarkup([[_back("alerts_menu", lng)]]), edit=True)
        else:
            await _send_msg(upd, ctx, t(lng, "sub_exists", cat=cat_name), reply_markup=InlineKeyboardMarkup([[_back("alerts_menu", lng)]]), edit=True)
            
    elif q.data == "my_subs":
        kws = db.user_keywords(uid)
        cats = db.user_subscriptions(uid)
        if not kws and not cats:
            await _send_msg(upd, ctx, t(lng, "no_subs"), reply_markup=InlineKeyboardMarkup([[_back("alerts_menu", lng)]]), edit=True)
            return
        m = "📋 *active subscription :*\n\n" if lng == "en" else "📋 *ንቁ የክትትል ማሳወቂያዎቼ:*\n\n"
        rows = []
        for c in cats:
            m += f"📂 Category: {c}\n" if lng == "en" else f"📂 ምድብ: {c}\n"
            rows.append([_b(f"❌ Remove {c}", f"unsub:{c}")])
        for k in kws:
            m += f"🔑 Keyword: {k}\n" if lng == "en" else f"🔑 ቃል: {k}\n"
            rows.append([_b(f"❌ Remove {k}", f"unkw:{k}")])
        rows.append([_back("alerts_menu", lng)])
        await _send_msg(upd, ctx, m, reply_markup=InlineKeyboardMarkup(rows), edit=True)
        
    elif q.data.startswith("unsub:"):
        cat_name = q.data.split(":", 1)[1]
        db._del2("subscriptions", "user_id", str(uid), "category", cat_name)
        await _send_msg(upd, ctx, t(lng, "unsub_done", cat=cat_name), reply_markup=InlineKeyboardMarkup([[_back("my_subs", lng)]]), edit=True)
        
    elif q.data.startswith("unkw:"):
        kw = q.data.split(":", 1)[1]
        db.remove_keyword(uid, kw)
        await _send_msg(upd, ctx, f"✅ Removed: {kw}", reply_markup=InlineKeyboardMarkup([[_back("my_subs", lng)]]), edit=True)
        
    elif q.data == "add_kw":
        ctx.user_data["action"] = "add_kw"
        await _send_msg(upd, ctx, t(lng, "kw_prompt"), reply_markup=InlineKeyboardMarkup([[_back("alerts_menu", lng)]]), edit=True)
        
    elif q.data == "cv_menu":
        kbd = InlineKeyboardMarkup([
            [_b(t(lng, "create_cv"), "cv_create"), _b(t(lng, "view_cv"), "cv_view")],
            [_b(t(lng, "match"), "cv_match"), _back("main_menu", lng)]
        ])
        await _send_msg(upd, ctx, t(lng, "cv_title"), reply_markup=kbd, edit=True)
        
    elif q.data == "cv_create":
        ctx.user_data["cv_step"] = 0
        ctx.user_data["payload"] = {}
        await _send_msg(upd, ctx, t(lng, CV_QUESTIONS[0]), edit=True)
        
    elif q.data == "cv_view":
        cv = db.get_cv(uid)
        if not cv:
            await _send_msg(upd, ctx, t(lng, "cv_none"), reply_markup=InlineKeyboardMarkup([[_back("cv_menu", lng)]]), edit=True)
            return
        m = (
            f"👤 *Name:* {cv.get('full_name')}\n"
            f"✉️ *Email:* {cv.get('email')}\n"
            f"📞 *Phone:* {cv.get('phone')}\n"
            f"📍 *Location:* {cv.get('location')}\n"
            f"📝 *Summary:* {cv.get('summary')}\n"
            f"🎓 *Education:* {cv.get('education')}\n"
            f"💼 *Experience:* {cv.get('experience')}\n"
            f"🛠 *Skills:* {cv.get('skills')}\n"
            f"🌐 *Languages:* {cv.get('languages')}"
        )
        await _send_msg(upd, ctx, m, reply_markup=InlineKeyboardMarkup([[_back("cv_menu", lng)]]), edit=True)
        
    elif q.data == "cv_match":
        await _send_msg(upd, ctx, t(lng, "matching"), edit=True)
        matches = match_jobs(uid)
        if not matches:
            await _send_msg(upd, ctx, t(lng, "no_matches"), reply_markup=InlineKeyboardMarkup([[_back("cv_menu", lng)]]), edit=False)
            return
        await q.message.delete()
        await _send_msg(upd, ctx, t(lng, "top_matches"), edit=False)
        for j in matches[:5]:
            await _send_msg(upd, ctx, _fmt_job(j, lng), reply_markup=_job_keyboard(j, lng, back_cb="cv_menu"), edit=False)
        await _send_msg(upd, ctx, t(lng, "listings_end"), reply_markup=InlineKeyboardMarkup([[_back("cv_menu", lng)]]), edit=False)
        
    elif q.data == "video_guide":
        kbd = InlineKeyboardMarkup([
            [_url(t(lng, "watch_video"), YOUTUBE_GUIDE_URL)], 
            [_back("online_menu", lng)]
        ])
        await _send_msg(upd, ctx, t(lng, "video_guide"), reply_markup=kbd, edit=True)
        
    elif q.data == "share_bot":
        share_txt = f"Find jobs from trusted platforms using this bot! t.me/{BOT_USERNAME}"
        if lng == "am":
            share_txt = f"ሙያ ሲከር  ቦትን በመጠቀም በቀላሉ ከታማኝ ምንጮች የተለያዩ የስራ እድሎችን በነፃ ያግኙ! t.me/{BOT_USERNAME}"
        enc_txt = urllib.parse.quote(share_txt)
        valid_share_url = f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text={enc_txt}"
        kbd = InlineKeyboardMarkup([
            [_url(t(lng, "share_bot"), valid_share_url)], 
            [_back("online_menu", lng)]
        ])
        await _send_msg(upd, ctx, t(lng, "share_bot"), reply_markup=kbd, edit=True)

async def text_handler(upd: Update, ctx):
  
    try:
        await ctx.bot.send_chat_action(chat_id=upd.effective_user.id, action=ChatAction.TYPING)
    except Exception:
        pass

    uid = upd.effective_user.id
    txt = upd.message.text.strip() if upd.message.text else ""
    if not txt: return
    
    act = ctx.user_data.get("action")
    step = ctx.user_data.get("cv_step")
    lng = db.get_lang(uid) or "en"

    if uid in ADMIN_IDS and act in ["broadcast", "broadcast_selected", "broadcast_keyword", "ban", "unban"]:
        ctx.user_data["action"] = None
        
        if act == "broadcast":
            users = db.get_all_users()
            await _send_msg(upd, ctx, f"📢 Transferring payload matrix to {len(users)} connections...", edit=False)
            count = 0
            for u in users:
                try:
                    await ctx.bot.send_message(chat_id=int(u.get("id")), text=f"📢 *MuyaSeeker*\n\n{txt}", parse_mode="Markdown")
                    count += 1
                    await asyncio.sleep(0.05)
                except: pass
            await _send_msg(upd, ctx, f"✅ Packet broadcast concluded to {count} active channels.", edit=False)
            
        elif act == "broadcast_selected":
            if ":" not in txt:
                await _send_msg(upd, ctx, "❌ Input structural layout constraint mismatch. Syntactic rule: `ID1,ID2 : Message text here`", edit=False)
                return
            ids_blob, body = txt.split(":", 1)
            try:
                targets = [int(i.strip()) for i in ids_blob.split(",") if i.strip().isdigit()]
            except:
                await _send_msg(upd, ctx, "❌ Numeric data parsing array fault.", edit=False)
                return
            await _send_msg(upd, ctx, f"🎯 Directing unique streams to {len(targets)} channels...", edit=False)
            count = 0
            for t_id in targets:
                try:
                    await ctx.bot.send_message(chat_id=t_id, text=f"📢 *MuyaSeeker*\n\n{body.strip()}", parse_mode="Markdown")
                    count += 1
                    await asyncio.sleep(0.05)
                except: pass
            await _send_msg(upd, ctx, f"✅ Targeted pipeline sequence processed to {count}/{len(targets)} targets.", edit=False)

        elif act == "broadcast_keyword":
            if ":" not in txt:
                await _send_msg(upd, ctx, "❌ Syntactic rule error. Format must be: `Keyword : Message here`", edit=False)
                return
            
            kw_target, body = txt.split(":", 1)
            kw_target = kw_target.strip().lower()
            body = body.strip()
            
            users = db.get_all_users()
            count = 0
            await _send_msg(upd, ctx, f"🎯 Scanning database for users watching the keyword or category: '{kw_target}'...", edit=False)
            
            for u in users:
                target_uid = int(u.get("id"))
                user_kws = [k.lower() for k in db.user_keywords(target_uid)]
                user_cats = [c.lower() for c in db.user_subscriptions(target_uid)]
                
                if kw_target in user_kws or kw_target in user_cats:
                    try:
                        await ctx.bot.send_message(chat_id=target_uid, text=f"🔔 *MuyaSeeker*\n\n{body}", parse_mode="Markdown")
                        count += 1
                        await asyncio.sleep(0.05)
                    except: pass
                    
            await _send_msg(upd, ctx, f"✅ Keyword payload successfully delivered to {count} matched channels.", edit=False)
            
        elif act == "ban":
            if not txt.isdigit():
                await _send_msg(upd, ctx, "❌ Target string data error. Requires numeric parameter ID.", edit=False)
                return
            db.ban_user(int(txt))
            await _send_msg(upd, ctx, f"🚫 Active database blocks built over ID: `{txt}`", edit=False)
            
        elif act == "unban":
            if not txt.isdigit():
                await _send_msg(upd, ctx, "❌ Target string data error. Requires numeric parameter ID.", edit=False)
                return
            db.unban_user(int(txt))
            await _send_msg(upd, ctx, f"✅ Clearance verified. Restriction dropped for ID: `{txt}`", edit=False)
        return

    if not await _guard(upd, ctx): return

    if act == "search":
        ctx.user_data["action"] = None
        res = db.search_jobs(txt)
        if not res:
            kbd = InlineKeyboardMarkup([[_b("🏠 Menu", "main_menu")]])
            await _send_msg(upd, ctx, t(lng, "no_results", q=txt), reply_markup=kbd, edit=False)
            return
        await _send_msg(upd, ctx, t(lng, "found", n=len(res), q=txt), edit=False)
        for j in res[:5]:
            await _send_msg(upd, ctx, _fmt_job(j, lng), reply_markup=_job_keyboard(j, lng, back_cb="main_menu"), edit=False)
        return

    if act == "add_kw":
        ctx.user_data["action"] = None
        kbd = InlineKeyboardMarkup([[_back("alerts_menu", lng)]])
        if db.add_keyword(uid, txt):
            await _send_msg(upd, ctx, t(lng, "kw_saved", kw=txt), reply_markup=kbd, edit=False)
        else:
            await _send_msg(upd, ctx, t(lng, "kw_exists", kw=txt), reply_markup=kbd, edit=False)
        return

    if step is not None:
        ctx.user_data["payload"][CV_FIELDS[step]] = txt
        step += 1
        if step >= len(CV_FIELDS):
            ctx.user_data["cv_step"] = None
            db.save_cv(uid, ctx.user_data["payload"])
            kbd = InlineKeyboardMarkup([[_b("🏠 Menu", "main_menu")]])
            await _send_msg(upd, ctx, t(lng, "cv_saved"), reply_markup=kbd, edit=False)
        else:
            ctx.user_data["cv_step"] = step
            await _send_msg(upd, ctx, t(lng, CV_QUESTIONS[step]), edit=False)
        return

    await show_main(upd, ctx, lng)

def main():
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("🚀 System Live Engine Online. Brand Profile: MuyaSeeker...")
    app.run_polling()

if __name__ == "__main__":
    main()
