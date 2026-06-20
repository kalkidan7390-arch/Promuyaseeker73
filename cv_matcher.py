import re
import db

def match_jobs(uid):
    cv = db.get_cv(uid)
    if not cv:
        return []
        
    cv_text = " ".join([
        str(cv.get("skills", "")),
        str(cv.get("experience", "")),
        str(cv.get("summary", "")),
        str(cv.get("education", "")),
        str(cv.get("full_name", ""))
    ]).lower()

    keywords = set(
        k.strip() for k in re.split(r"[,\s\n\r\t;/]+", cv_text)
        if len(k.strip()) >= 3
    )
    
    stop_words = {"the","and","for","are","was","with","has","have",
                  "this","that","from","been","they","will","also"}
    keywords -= stop_words

    jobs = db._all("jobs")
    scored = []
    
    for job in jobs:
        if str(job.get("is_active", "false")).lower() != "true":
            continue
 
        job_text = " ".join([
            str(job.get("title", "")),
            str(job.get("description", "")),
            str(job.get("category", "")),
            str(job.get("company", "")),
            str(job.get("education_level", "")),
            str(job.get("language", "")),
            str(job.get("experience", "")),
            str(job.get("gender", ""))
        ]).lower()
        
        score = sum(1 for k in keywords if k in job_text)
        if score > 0:
            scored.append((score, job))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored]
