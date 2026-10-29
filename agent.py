import asyncio, os, json, csv, datetime
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from pypdf import PdfReader
from browser_use import Agent, Browser, ChatOpenAI

load_dotenv()

# ================== تنظیمات ==================
SITES = [
    {"name": "Jobinja",     "url": "https://jobinja.ir/jobs",       "query": "python,backend python, full stack developer, frontend react"},
    {"name": "JobVision",   "url": "https://jobvision.ir",          "query": "python,backend python, full stack developer, frontend react"},
    {"name": "e-estekhdam", "url": "https://www.e-estekhdam.com/",  "query": "python,backend python, full stack developer, frontend react"},
]
MAX_APPS_PER_SITE = 5
CITY = "Tehran"
QUERY_OVERRIDE = os.getenv("JOB_QUERY", "").strip()

EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
EDGE_PATH = next((p for p in EDGE_PATHS if os.path.exists(p)), None)
if not EDGE_PATH:
    raise SystemExit("Edge پیدا نشد. مسیر msedge.exe را در EDGE_PATHS اضافه کنید.")
# =============================================

class Applied(BaseModel):
    title: str
    company: str
    url: str

class Skipped(BaseModel):
    title: str
    reason: str

class Report(BaseModel):
    applied: List[Applied]
    skipped: List[Skipped]

# رزومه: همان فایل ثابت برای آپلود (بدون تغییر)
RESUME_PATH = os.path.abspath("resume.pdf")
try:
    resume_text = "\n".join((p.extract_text() or "") for p in PdfReader("resume.pdf").pages)
except Exception as e:
    print(f"خواندن resume.pdf ممکن نیست ({e}). از resume.txt استفاده می‌شود.")
    resume_text = open("resume.txt", encoding="utf-8").read()

profile = json.load(open("profile.json", encoding="utf-8"))

llm = ChatOpenAI(
    model=os.getenv("GAPGPT_MODEL", "gpt-4o"),
    api_key=os.getenv("GAPGPT_API_KEY"),
    base_url=os.getenv("GAPGPT_BASE_URL"),
)

def build_task(site):
    query = QUERY_OVERRIDE or site["query"]
    return f"""
Go to {site['url']} and search for: "{query}".
Use the site's city/location filter to select "{CITY}" (تهران) before applying, if such a filter exists.
Apply to up to {MAX_APPS_PER_SITE} jobs that fit the candidate's resume, and submit each application yourself.

RULES:
- Use ONLY facts from the resume/profile below. Never invent experience, degrees or skills.
- Upload the existing resume file from: {RESUME_PATH}. Upload it as-is.
- NEVER edit, update, replace, delete or re-create the resume or profile stored on the site/account. Do not change any profile fields or account settings. Only upload the file during an application, and if the site asks to change the stored profile, skip that job and note it.
- If a required question can't be answered from the data, skip that job and note why.
- If login is needed and you are not logged in, or there is a CAPTCHA/2FA you can't pass, stop and report it as skipped.
- Do not apply to the same job twice.
- Return the final report as JSON: applied (title, company, url) and skipped (title, reason).
- Only apply to jobs located in Tehran (شهر تهران). Skip any job whose location is outside Tehran, and for remote jobs, skip too unless the location says Tehran. Note "location outside Tehran" as the skip reason.

PROFILE: {json.dumps(profile, ensure_ascii=False)}
RESUME:
{resume_text}
"""

def log(site, status, title="", company="", url="", note=""):
    new = not os.path.exists("applications.csv")
    with open("applications.csv", "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "site", "status", "title", "company", "url", "note"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"),
                    site, status, title, company, url, note])

async def run_site(site):
    browser = Browser(
        executable_path=EDGE_PATH,
        user_data_dir=f"./browser_profile_{site['name']}",  # هر سایت پروفایل جدا
        headless=False,
        keep_alive=False,
    )
    try:
        agent = Agent(
            task=build_task(site), llm=llm, browser=browser,
            available_file_paths=[RESUME_PATH],
            output_model_schema=Report,
            use_vision=False,
        )
        history = await agent.run(max_steps=60)
        raw = history.final_result()
        if not raw:
            log(site["name"], "error", note="no result returned")
            return
        rep = Report.model_validate_json(raw)
        for a in rep.applied:
            log(site["name"], "applied", a.title, a.company, a.url)
        for s in rep.skipped:
            log(site["name"], "skipped", s.title, note=s.reason)
        print(f"[{site['name']}] applied={len(rep.applied)} skipped={len(rep.skipped)}")
    except Exception as e:
        log(site["name"], "error", note=str(e)[:200])
        print(f"[{site['name']}] error: {e}")
    finally:
        await browser.kill()

async def main():
    # همه سایت‌ها هم‌زمان اجرا می‌شوند
    await asyncio.gather(*(run_site(site) for site in SITES))

if __name__ == "__main__":
    asyncio.run(main())
