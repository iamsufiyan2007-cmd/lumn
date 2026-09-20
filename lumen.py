"""Lumn Study Smart: AI quizzes, progress tracking and a tutor for students and teachers.

Run:      streamlit run app.py
Install:  pip install streamlit plotly
Secrets (.streamlit/secrets.toml):
    GOOGLE_API_KEY_1 = "..."
    GOOGLE_API_KEY_2 = "..."      # optional, used by the tutor chat
    TEACHER_CODE     = "..."      # optional, enables teacher sign-up
"""
import hashlib
import html
import json
import os
import secrets
import smtplib
import sqlite3
import time
from urllib.parse import quote_plus
from datetime import date, timedelta
from email.message import EmailMessage

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Lumn Study Smart", page_icon="🦉", layout="wide", initial_sidebar_state="expanded")

DB, MODEL, DAILY_GOAL = os.environ.get("STUDYSMART_DB", "studysmart.db"), "gemini-2.5-flash", 5
GREY = "#5b6f79"
GREEN, BLUE, RED, ORANGE, PURPLE = "#58cc02", "#1cb0f6", "#ff4b4b", "#ff9600", "#ce82ff"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;800;900&display=swap');
:root { --bg:#131f24; --card:#202f36; --line:#37464f; --text:#dce6ec; --muted:#8fa3ad; --green:#58cc02; --blue:#1cb0f6; --orange:#ff9600; }
html, body, .stApp, .stMarkdown, p, li, label, button, input, textarea, h1, h2, h3 { font-family: 'Nunito', system-ui, 'Segoe UI', sans-serif; }
[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
.stApp { background: radial-gradient(900px 500px at 85% -10%, rgba(28,176,246,.10), transparent 60%), radial-gradient(800px 500px at -10% 105%, rgba(88,204,2,.08), transparent 60%), var(--bg); background-attachment: fixed; color: var(--text); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.5rem; max-width: 1500px; }
h1, h2, h3 { font-weight: 900 !important; color: #fff; letter-spacing: -.01em; }
[data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"] { color: var(--muted); font-weight: 700; }
@keyframes rise  { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: none; } }
@keyframes pop   { 0% { transform: scale(.88); } 60% { transform: scale(1.05); } 100% { transform: scale(1); } }
@keyframes bob   { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
@keyframes flame { 0%, 100% { transform: scale(1) rotate(-3deg); } 50% { transform: scale(1.15) rotate(3deg); } }
.card { background: var(--card); border: 2px solid var(--line); border-bottom-width: 5px; border-radius: 18px;
        padding: 18px 22px; margin-bottom: 14px; color: var(--text); }
.stat { text-align: center; animation: pop .45s ease both; }
.stat .ico { font-size: 2rem; } .stat .val { font-size: 2.1rem; font-weight: 900; line-height: 1.15; }
.stat .lab { color: var(--muted); font-weight: 700; }
.fire { display: inline-block; animation: flame 1.2s ease-in-out infinite; }
.hero { text-align: center; padding: 8px 0 22px; }
.hero .owl { font-size: 4.8rem; display: inline-block; animation: bob 2.4s ease-in-out infinite;
             filter: drop-shadow(0 0 22px rgba(88,204,2,.4)); }
.hero p { color: var(--muted); font-weight: 700; font-size: 1.1rem; }
.q { font-size: 1.4rem; font-weight: 800; color: #fff; animation: rise .35s ease both; }
.bar { height: 16px; background: var(--line); border-radius: 99px; overflow: hidden; margin-bottom: 6px; }
.bar > div { height: 100%; background: linear-gradient(90deg, #58cc02, #89e219); border-radius: 99px; transition: width .6s ease; }
.fb { border-radius: 16px; padding: 16px 20px; margin: 12px 0; font-weight: 700; animation: rise .3s ease both; }
.fb.ok   { background: rgba(88,204,2,.15);  color: #9be82f; border: 2px solid #58a700; }
.fb.part { background: rgba(255,150,0,.15); color: #ffb84d; border: 2px solid #b36b00; }
.fb.bad  { background: rgba(255,75,75,.15); color: #ff8080; border: 2px solid #b83232; }
.chip { background: var(--card); border: 2px solid var(--line); border-radius: 14px; padding: 10px 14px; margin-bottom: 12px; color: var(--text); }
[data-testid="stSidebar"] { background: #0f181c; border-right: 2px solid var(--line); }
.stButton > button, .stDownloadButton > button { border-radius: 14px; font-weight: 800; background: var(--card); color: var(--text);
        border: 2px solid var(--line); border-bottom: 5px solid var(--line); padding: .55rem 1.3rem;
        transition: transform .12s ease, border-color .12s ease, background .12s ease; }
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-2px); border-color: var(--blue); color: var(--blue); }
.stButton > button:active { transform: translateY(3px); border-bottom-width: 2px; }
.stButton > button[data-testid="stBaseButton-primary"], .stButton > button[kind="primary"] {
        background: var(--green); color: #10230a; border-color: #58a700; }
.stButton > button[data-testid="stBaseButton-primary"]:hover, .stButton > button[kind="primary"]:hover { background: #6ee00a; color: #10230a; }
.stButton > button:disabled { background: var(--card); color: #5b6f79; border-color: var(--line); transform: none; }
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div { border-radius: 12px !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within { border-color: var(--blue) !important; }
[data-baseweb="tab"] { font-weight: 800; }
[data-baseweb="tab-highlight"] { background: var(--green) !important; height: 4px; border-radius: 4px; }
[data-testid="stRadio"] div[role="radiogroup"] > label { background: var(--card); border: 2px solid var(--line); border-bottom-width: 4px;
        border-radius: 14px; padding: 11px 16px; margin-bottom: 6px; transition: border-color .12s ease, background .12s ease; }
[data-testid="stRadio"] div[role="radiogroup"] > label:hover { border-color: var(--blue); }
[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) { border-color: var(--blue); background: rgba(28,176,246,.16); }
[data-testid="stPlotlyChart"] { background: var(--card); border: 2px solid var(--line); border-radius: 18px; padding: 6px; }
[data-testid="stMetric"] { background: var(--card); border: 2px solid var(--line); border-radius: 16px; padding: 12px 16px; }
@keyframes grow { from { width: 0; } }
.fill { width: var(--w); animation: grow .9s cubic-bezier(.2,.8,.2,1) both; }
.sub { margin-bottom: 14px; } .sub:last-child { margin-bottom: 0; }
.subhead { display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 6px; color: var(--text); }
.subhead span { color: var(--muted); }
.card h3 { margin: 0 0 14px; font-size: 1.15rem; }
.ring { width: 124px; height: 124px; border-radius: 50%; margin: 6px auto 12px; display: grid; place-items: center; position: relative;
        background: conic-gradient(var(--green) var(--deg), var(--line) 0); animation: pop .6s ease both; }
.ring::before { content: ""; position: absolute; inset: 12px; border-radius: 50%; background: var(--card); }
.ring span { position: relative; font-weight: 900; font-size: 1.6rem; color: #fff; }
.week { display: flex; justify-content: space-between; }
.day { text-align: center; color: var(--muted); font-weight: 800; }
.dot { width: 40px; height: 40px; border-radius: 50%; background: var(--line); display: grid; place-items: center; margin-bottom: 4px; }
.day.on .dot { background: rgba(255,150,0,.22); border: 2px solid var(--orange); }
.badges { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.badge { text-align: center; padding: 10px 4px; border-radius: 14px; background: #182830; color: #5b6f79; font-weight: 800; font-size: .85rem; }
.badge.on { background: rgba(88,204,2,.12); color: #9be82f; animation: pop .5s ease both; }
.bi { font-size: 1.8rem; }
.lb { display: flex; gap: 12px; align-items: center; padding: 8px 10px; border-radius: 12px; }
.lb b { flex: 1; color: #fff; } .lb span { color: var(--muted); font-weight: 800; }
.lb.me { background: rgba(28,176,246,.16); }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label { width: 100%; font-weight: 800; padding: 13px 16px; }
.mini { font-weight: 700; } .mini small { color: var(--muted); }
[data-testid="stForm"] { background: var(--card); border: 2px solid var(--line); border-radius: 18px; }
.stFormSubmitButton > button { border-radius: 14px; font-weight: 800; background: var(--green); color: #10230a; border: 2px solid #58a700; border-bottom: 5px solid #58a700; }
.stFormSubmitButton > button:hover { background: #6ee00a; color: #10230a; }
.msg { display: flex; gap: 12px; margin: 10px 0; animation: rise .3s ease both; }
.msg.me { flex-direction: row-reverse; }
.av { flex: 0 0 46px; height: 46px; border-radius: 50%; background: var(--card); border: 3px solid var(--line); display: grid; place-items: center; font-size: 1.5rem; }
.bub { background: var(--card); border: 2px solid var(--line); border-radius: 16px; padding: 10px 14px; color: var(--text); max-width: 680px; }
.who { font-weight: 900; font-size: .85rem; margin-bottom: 3px; } .who small { color: var(--muted); font-weight: 700; }
.room { display: flex; gap: 12px; margin-bottom: 14px; }
.rm { flex: 1; text-align: center; padding: 12px; border-radius: 16px; background: var(--card); border: 2px solid var(--line); display: flex; flex-direction: column; transition: box-shadow .3s ease, border-color .3s ease; }
.rm .big { font-size: 2.6rem; animation: bob 2.4s ease-in-out infinite; }
.rm b { color: var(--c); } .rm small { color: var(--muted); font-weight: 700; }
.rm.on { border-color: var(--c); box-shadow: 0 0 14px var(--c); }
.steps { display: flex; gap: 10px; margin-bottom: 16px; }
.step { flex: 1; text-align: center; padding: 10px; border-radius: 14px; background: var(--card); border: 2px solid var(--line); font-weight: 800; color: var(--muted); }
.step.on { border-color: var(--blue); color: #fff; background: rgba(28,176,246,.16); }
.step.done { border-color: var(--green); color: #9be82f; }
.timer { font-size: 2.6rem; font-weight: 900; text-align: center; line-height: 1.1; margin-bottom: 8px; }
.kw { display: inline-block; background: rgba(206,130,255,.15); color: #e0b3ff; border-radius: 99px; padding: 3px 12px; margin: 3px 4px 0 0; font-weight: 700; }
footer { visibility: hidden; } [data-testid="stDecoration"] { display: none; }
* { scrollbar-width: thin; scrollbar-color: #37464f transparent; }
::selection { background: rgba(88,204,2,.35); }
.card, .bub, .q, .fb { overflow-wrap: anywhere; }
button:focus-visible, a:focus-visible { outline: 3px solid rgba(28,176,246,.55) !important; outline-offset: 2px; }
.hero h1 { background: linear-gradient(90deg, #58cc02, #1cb0f6); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.stLinkButton > a { border-radius: 14px; font-weight: 800; background: var(--card); color: var(--text); border: 2px solid var(--line);
        border-bottom: 5px solid var(--line); transition: transform .12s ease, border-color .12s ease; }
.stLinkButton > a:hover { transform: translateY(-2px); border-color: var(--blue); color: var(--blue); }
[data-testid="stChatMessage"] { background: var(--card); border: 2px solid var(--line); border-radius: 16px; }
[data-testid="stChatInput"] { border-radius: 16px; }
.room, .steps { flex-wrap: wrap; } .rm { min-width: 110px; } .step { min-width: 130px; }
@media (max-width: 768px) {
  .block-container { padding: 1.2rem .8rem 4rem; }
  .hero .owl { font-size: 3.4rem; } .stat .val { font-size: 1.6rem; } .rm .big { font-size: 2rem; }
  .badges { grid-template-columns: repeat(2, 1fr); } .bub { max-width: 100%; } .ring { width: 104px; height: 104px; }
}
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style>
"""


# ------------------------------------------------------------------ storage
def _connect():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c


def run(sql, args=()):
    """Run one SQL statement and return all rows."""
    c = _connect()
    try:
        with c:
            return c.execute(sql, args).fetchall()
    finally:
        c.close()


def frame(sql, args=()):
    """Run a query and return a DataFrame."""
    c = _connect()
    try:
        return pd.read_sql_query(sql, c, params=args)
    finally:
        c.close()


def bump():
    """Invalidate cached answer tables after a write."""
    st.session_state["ver"] = st.session_state.get("ver", 0) + 1


@st.cache_data(show_spinner=False, max_entries=512)
def answers_for(username, ver):
    return frame("SELECT * FROM answers WHERE username=?", (username,))


@st.cache_data(ttl=20, show_spinner=False)
def leaderboard_rows():
    return frame("""SELECT a.username, CAST(SUM(a.score) * 10 AS INTEGER) AS xp FROM answers a
                    JOIN users u ON u.username = a.username WHERE u.role = 'student'
                    GROUP BY a.username ORDER BY xp DESC LIMIT 5""")


@st.cache_data(ttl=15, show_spinner=False)
def class_answers():
    return frame("SELECT a.* FROM answers a JOIN users u ON u.username=a.username WHERE u.role='student'")


@st.cache_resource(show_spinner=False)
def init_db():
    c = _connect()
    c.execute("PRAGMA journal_mode=WAL")
    with c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users(
                username TEXT PRIMARY KEY, email TEXT, salt TEXT, pw TEXT, role TEXT,
                age INTEGER, level TEXT, syllabus TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS answers(
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, subject TEXT, kind TEXT,
                question TEXT, given TEXT, expected TEXT, score REAL, feedback TEXT, ts TEXT);
            CREATE TABLE IF NOT EXISTS mock_results(
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, stage TEXT, score REAL, feedback TEXT,
                ts TEXT DEFAULT (datetime('now','localtime')));
            CREATE INDEX IF NOT EXISTS idx_answers_user ON answers(username);
            CREATE INDEX IF NOT EXISTS idx_mock_user ON mock_results(username);
        """)
    c.close()


def secret(name, default=""):
    try:
        return st.secrets[name]
    except Exception:
        return default


def hash_pw(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 150_000).hex()


def register(username, email, pw, role, age, level, syllabus):
    """Create an account. Returns an error message, or None on success."""
    if run("SELECT 1 FROM users WHERE username=?", (username,)):
        return "That username is already taken."
    salt = secrets.token_hex(16)
    run("INSERT INTO users(username,email,salt,pw,role,age,level,syllabus) VALUES (?,?,?,?,?,?,?,?)",
        (username, email, salt, hash_pw(pw, salt), role, age, level, syllabus))


def authenticate(username, pw):
    rows = run("SELECT * FROM users WHERE username=?", (username,))
    if rows and secrets.compare_digest(rows[0]["pw"], hash_pw(pw, rows[0]["salt"])):
        return {k: rows[0][k] for k in ("username", "email", "role", "age", "level", "syllabus")}


def otp_ready():
    return bool(secret("SMTP_USER") and secret("SMTP_PASS"))


def send_otp(email):
    """Email a 6-digit code (valid 10 minutes). Returns an error message, or None."""
    ss = st.session_state
    if time.time() - ss.get("otp_sent", 0) < 30:
        return "Please wait 30 seconds before asking for another code."
    code = f"{secrets.randbelow(10 ** 6):06d}"
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = f"Your Lumn code: {code}", secret("SMTP_USER"), email
    msg.set_content(f"Your Lumn verification code is {code}. It expires in 10 minutes.\nIf you did not ask for it, ignore this email.")
    try:
        with smtplib.SMTP_SSL(secret("SMTP_HOST", "smtp.gmail.com"), 465, timeout=15) as smtp:
            smtp.login(secret("SMTP_USER"), secret("SMTP_PASS"))
            smtp.send_message(msg)
    except Exception as e:
        return f"Could not send the email ({e})."
    ss.otp = dict(email=email.lower(), hash=hashlib.sha256(code.encode()).hexdigest(), exp=time.time() + 600, tries=0)
    ss.otp_sent = time.time()


def check_otp(email, code):
    """Returns an error message, or None if the code is right."""
    o = st.session_state.get("otp")
    if not o or o["email"] != email.lower():
        return "Ask for a code first."
    if time.time() > o["exp"]:
        return "That code has expired. Ask for a new one."
    if o["tries"] >= 5:
        return "Too many wrong tries. Ask for a new code."
    o["tries"] += 1
    if not secrets.compare_digest(o["hash"], hashlib.sha256(code.strip().encode()).hexdigest()):
        return "Wrong code."
    del st.session_state["otp"]


def mistakes(username, limit=8):
    """Questions the student has only ever got wrong, as typed-answer items."""
    d = frame("""SELECT subject, question, expected FROM answers WHERE username=? GROUP BY question
                 HAVING MAX(score) < 0.99 ORDER BY MAX(id) DESC LIMIT ?""", (username, limit))
    return [dict(subject=r.subject, kind="short", question=r.question, answer=r.expected, explanation="")
            for r in d.itertuples()]


def save_answer(user, item, given, score, feedback):
    run("""INSERT INTO answers(username,subject,kind,question,given,expected,score,feedback,ts)
           VALUES (?,?,?,?,?,?,?,?,datetime('now','localtime'))""",
        (user, item["subject"], item["kind"], item["question"], str(given), item["answer"], score, feedback))
    bump()


# ---------------------------------------------------------------------- AI
@st.cache_resource
def _http():
    import requests
    return requests.Session()


def ai(prompt, json_mode=False, key="GOOGLE_API_KEY_1"):
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    if json_mode:
        body["generationConfig"] = {"responseMimeType": "application/json"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    for attempt in range(2):
        r = _http().post(url, json=body, headers={"x-goog-api-key": st.secrets[key]}, timeout=45)
        if r.status_code in (429, 500, 503) and attempt == 0:
            time.sleep(1.5)
            continue
        break
    r.raise_for_status()
    return "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])


def as_list(x, keys=()):
    """Coerce model output into a list of dicts that contain the given keys."""
    if isinstance(x, dict):
        x = next((v for v in x.values() if isinstance(v, list)), [])
    return [d for d in x if isinstance(d, dict) and all(k in d for k in keys)]


def parse_subjects(syllabus):
    return [s.strip() for s in syllabus.replace(",", "/").split("/") if s.strip()]


def make_quiz(subjects, level, per_subject, extra=None):
    prompt = extra or f"""Create a quiz for a student at this level: {level}. Subjects: {subjects}.
For each subject write {per_subject} questions. About 60% are multiple choice (kind "mcq", exactly 4 options,
"answer" must be identical to one option). The rest are written answers (kind "short", no options, "answer" is a
model answer in one or two sentences). Match the difficulty to the level.
Return only a JSON array of objects with keys: subject (one of the given subjects), kind, question, options,
answer, explanation. Use plain ASCII and no newlines inside strings."""
    items = []
    for d in as_list(json.loads(ai(prompt, json_mode=True)), ("question", "answer")):
        try:
            d["kind"] = d.get("kind", "short")
            d["explanation"] = d.get("explanation", "")
            if d["kind"] == "mcq":
                d["options"] = [str(o) for o in d["options"]]
                if d["answer"] not in d["options"]:
                    continue
            items.append(d)
        except (KeyError, TypeError):
            continue
    return items


def grade_short(question, expected, given):
    """Grade a typed answer. Returns (score 0-1, feedback)."""
    prompt = f"""Grade a student's written answer. Accept correct answers even if worded differently.
Question: {question}
Reference answer: {expected}
Student answer: {given}
Return JSON: {{"score": 1 if correct, 0.5 if partly correct, 0 if wrong, "feedback": "one short encouraging sentence"}}"""
    try:
        r = json.loads(ai(prompt, json_mode=True))
        return float(r["score"]), str(r["feedback"])
    except Exception:
        ok = given.strip().lower() == expected.strip().lower()
        return float(ok), "Auto-checked (AI grader unavailable)."


# ------------------------------------------------------------------- stats
def streak(timestamps):
    days, n, cur = {t[:10] for t in timestamps}, 0, date.today()
    if str(cur) not in days:
        cur -= timedelta(days=1)
    while str(cur) in days:
        n, cur = n + 1, cur - timedelta(days=1)
    return n


def summary(df):
    if df.empty:
        return dict(n=0, acc=0, xp=0, streak=0, subj=pd.Series(dtype=float))
    return dict(n=len(df), acc=round(df.score.mean() * 100), xp=int(df.score.sum() * 10),
                streak=streak(df.ts), subj=(df.groupby("subject").score.mean() * 100).round(1))


# ------------------------------------------------------------------ charts
def show(fig, h=340):
    line, text = "#37464f", "#dce6ec"
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Nunito", size=14, color=text),
                      title_font=dict(size=18, color="#ffffff"), transition=dict(duration=600))
    fig.update_xaxes(gridcolor=line, zerolinecolor=line)
    fig.update_yaxes(gridcolor=line, zerolinecolor=line)
    fig.update_polars(bgcolor="rgba(0,0,0,0)", radialaxis_gridcolor=line, angularaxis_gridcolor=line,
                      radialaxis_tickfont_color=text, angularaxis_tickfont_color=text)
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:  # older Streamlit versions
        st.plotly_chart(fig, use_container_width=True)


def charts(df):
    import plotly.graph_objects as go
    s = summary(df)["subj"]
    a, b = st.columns(2)
    with a:
        if len(s) >= 3:
            fig = go.Figure(go.Scatterpolar(r=list(s) + [s.iloc[0]], theta=list(s.index) + [s.index[0]],
                                            fill="toself", line_color=BLUE, fillcolor="rgba(28,176,246,.25)"))
            fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), title="Skill map")
            show(fig)
        else:
            st.markdown('<div class="card">Practise three or more subjects to unlock your skill map.</div>',
                        unsafe_allow_html=True)
    with b:
        colors = [GREEN if v >= 75 else ORANGE if v >= 50 else RED for v in s]
        fig = go.Figure(go.Bar(x=s.values, y=s.index, orientation="h", marker_color=colors,
                               text=[f"{v:.0f}%" for v in s], textposition="outside"))
        fig.update_layout(title="Accuracy by subject", xaxis=dict(range=[0, 110], title="%"))
        show(fig)
    c, d = st.columns([3, 2])
    with c:
        t = df.assign(day=df.ts.str[:10]).groupby("day").score.mean() * 100
        fig = go.Figure(go.Scatter(x=t.index, y=t.values, mode="lines+markers", line=dict(color=GREEN, width=4, shape="spline"),
                                   marker=dict(size=10), fill="tozeroy", fillcolor="rgba(88,204,2,.15)"))
        fig.update_layout(title="Daily accuracy", yaxis=dict(range=[0, 105], title="%"))
        show(fig)
    with d:
        full, part = int((df.score >= .99).sum()), int(((df.score >= .5) & (df.score < .99)).sum())
        fig = go.Figure(go.Pie(labels=["Correct", "Partly", "Wrong"], values=[full, part, len(df) - full - part],
                               hole=.6, marker_colors=[GREEN, ORANGE, RED], sort=False))
        fig.update_layout(title="Answer mix", legend=dict(orientation="h"))
        show(fig)


# ------------------------------------------------------------------- pages
def mastery_html(user, df):
    got = {k.lower(): v for k, v in summary(df)["subj"].items()}
    rows = ""
    for sub in parse_subjects(user["syllabus"]):
        v = next((x for k, x in got.items() if k == sub.lower() or k in sub.lower() or sub.lower() in k), None)
        color = GREY if v is None else GREEN if v >= 75 else ORANGE if v >= 50 else RED
        label = "not started" if v is None else f"{v:.0f}%"
        rows += (f'<div class="sub"><div class="subhead"><b>{esc(sub)}</b><span>{label}</span></div>'
                 f'<div class="bar"><div class="fill" style="--w:{v or 0}%;background:{color}"></div></div></div>')
    return f'<div class="card"><h3>Subject mastery</h3>{rows}</div>'


def goal_html(df):
    n = int((df.ts.str[:10] == str(date.today())).sum()) if not df.empty else 0
    msg = "Daily goal reached! 🎉" if n >= DAILY_GOAL else f"{DAILY_GOAL - n} more answers to hit today's goal"
    return (f'<div class="card stat"><h3>Daily goal</h3><div class="ring" style="--deg:{min(n / DAILY_GOAL, 1) * 360:.0f}deg">'
            f'<span>{min(n, DAILY_GOAL)}/{DAILY_GOAL}</span></div><div class="lab">{msg}</div></div>')


def week_html(df):
    days = {t[:10] for t in df.ts} if not df.empty else set()
    cells = ""
    for k in range(6, -1, -1):
        d = date.today() - timedelta(days=k)
        on = str(d) in days
        cells += f'<div class="day{" on" if on else ""}"><div class="dot">{"🔥" if on else ""}</div>{d.strftime("%a")[0]}</div>'
    return f'<div class="card"><h3>This week</h3><div class="week">{cells}</div></div>'


def leaderboard_html(me):
    d = leaderboard_rows()
    medals = ["🥇", "🥈", "🥉", "4", "5"]
    rows = "".join(f'<div class="lb{" me" if r.username == me else ""}"><span>{medals[i]}</span>'
                   f'<b>{esc(r.username)}</b><span>{r.xp} XP</span></div>' for i, r in enumerate(d.itertuples()))
    return f'<div class="card"><h3>Leaderboard</h3>{rows or "Be the first on the board!"}</div>'


def badges_html(s):
    defs = [("🌱", "First steps", s["n"] >= 1), ("🔥", "3-day streak", s["streak"] >= 3), ("⚡", "100 XP", s["xp"] >= 100),
            ("🎯", "Sharp mind", s["n"] >= 10 and s["acc"] >= 80), ("🧭", "All-rounder", len(s["subj"]) >= 3),
            ("💯", "50 answers", s["n"] >= 50)]
    tiles = "".join(f'<div class="badge{" on" if ok else ""}"><div class="bi">{ico if ok else "🔒"}</div>{name}</div>'
                    for ico, name, ok in defs)
    return f'<div class="card"><h3>Achievements</h3><div class="badges">{tiles}</div></div>'


def go_to(page):
    st.session_state.nav = page


def esc(x):
    """Escape text for HTML blocks: keeps blank lines and $ signs from breaking Streamlit markdown."""
    return html.escape(str(x)).replace("\n", "<br>").replace("$", "&#36;")


def finish_signup(u, email, p, role, age, level, syl):
    err = register(u.strip(), email.strip(), p, role, int(age), level.strip(), syl.strip())
    if err:
        st.error(err)
        return
    st.session_state.pop("su_wait", None)
    st.session_state.user = authenticate(u.strip(), p)
    st.rerun()


def auth_page():
    st.markdown('<div class="hero"><div class="owl">🦉</div><h1>Lumn Study Smart</h1>'
                '<p>Learn a little every day. Quizzes, streaks and a tutor that knows your weak spots.</p></div>',
                unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid:
        tabs = st.tabs(["Log in", "Create account"] + (["Forgot password"] if otp_ready() else []))
        with tabs[0]:
            u = st.text_input("Username", key="li_u")
            p = st.text_input("Password", type="password", key="li_p")
            if st.button("Log in", type="primary", key="li_b"):
                user = authenticate(u.strip(), p)
                if user:
                    st.session_state.user = user
                    st.rerun()
                st.error("Wrong username or password.")
        with tabs[1]:
            role = "student"
            if secret("TEACHER_CODE"):
                role = st.radio("I am a", ["student", "teacher"], horizontal=True, key="su_r")
            u = st.text_input("Username", key="su_u")
            email = st.text_input("Email", key="su_e")
            p = st.text_input("Password (6+ characters)", type="password", key="su_p")
            age = st.number_input("Age", 4, 100, 16, key="su_a")
            level = st.text_input("Your level", placeholder="e.g. Grade 10, College year 1", key="su_l")
            syl = st.text_input("Subjects, separated by /", placeholder="Maths/English/Science", key="su_s")
            code = st.text_input("Teacher code", type="password", key="su_c") if role == "teacher" else ""
            if st.button("Create account", type="primary", key="su_b"):
                problem = ("Use a password with at least 6 characters." if len(p) < 6 else
                           "Fill in every field." if not u.strip() or (role == "student" and not (level.strip() and syl.strip())) else
                           "That teacher code is not right." if role == "teacher" and code != secret("TEACHER_CODE") else
                           "Enter a valid email so we can send you a code." if otp_ready() and "@" not in email else "")
                if problem:
                    st.error(problem)
                elif otp_ready():
                    err = send_otp(email.strip())
                    if err:
                        st.error(err)
                    else:
                        st.session_state.su_wait = True
                        st.success(f"We sent a 6-digit code to {email.strip()}.")
                else:
                    finish_signup(u, email, p, role, age, level, syl)
            if st.session_state.get("su_wait"):
                c = st.text_input("6-digit code from your email", key="su_code")
                if st.button("Verify and create account", type="primary", key="su_v"):
                    err = check_otp(email.strip(), c)
                    if err:
                        st.error(err)
                    else:
                        finish_signup(u, email, p, role, age, level, syl)
        if len(tabs) > 2:
            with tabs[2]:
                ru = st.text_input("Username", key="rp_u")
                rm = st.text_input("Email on the account", key="rp_e")
                if st.button("Send code", key="rp_s"):
                    row = run("SELECT email FROM users WHERE username=?", (ru.strip(),))
                    if row and row[0]["email"].lower() == rm.strip().lower():
                        err = send_otp(rm.strip())
                        if err:
                            st.error(err)
                    st.info("If those details match an account, a code is on its way.")
                rc = st.text_input("6-digit code", key="rp_c")
                rn = st.text_input("New password (6+ characters)", type="password", key="rp_n")
                if st.button("Reset password", type="primary", key="rp_b"):
                    err = "Use a password with at least 6 characters." if len(rn) < 6 else check_otp(rm.strip(), rc)
                    if err:
                        st.error(err)
                    else:
                        salt = secrets.token_hex(16)
                        run("UPDATE users SET salt=?, pw=? WHERE username=? AND lower(email)=lower(?)",
                            (salt, hash_pw(rn, salt), ru.strip(), rm.strip()))
                        st.success("Password changed. You can log in now.")


OWLS = {"Hoot": dict(color=BLUE, role="HR lead"), "Wisp": dict(color=PURPLE, role="Tech lead"),
        "Sage": dict(color=ORANGE, role="Hiring manager")}
STAGES = ["Group discussion", "Aptitude test", "Interview"]
IV_ORDER = ["Hoot", "Wisp", "Sage", "Hoot", "Wisp", "Sage"]
GD_TURNS, APT_SECONDS = 4, 45
ICONS = {"Home": "🏠", "Practice": "✏️", "Study Mode": "📖", "Mock Interview": "🎤", "Progress": "📊",
         "Tutor": "💡", "Class": "🏫"}


def sidebar(user, df):
    s = summary(df)
    n = int((df.ts.str[:10] == str(date.today())).sum()) if not df.empty else 0
    with st.sidebar:
        st.markdown(f'<div class="chip">🦉 <b>{esc(user["username"])}</b><br>'
                    f'<small>{esc(user["role"].title())}</small></div>', unsafe_allow_html=True)
        pages = ["Home", "Practice", "Study Mode", "Mock Interview", "Progress", "Tutor"] + (["Class"] if user["role"] == "teacher" else [])
        page = st.radio("Menu", pages, key="nav", label_visibility="collapsed", format_func=lambda p: f"{ICONS[p]}  {p}")
        st.markdown(f'<div class="card mini">🔥 <b>{s["streak"]}</b> day streak &nbsp; ⚡ <b>{s["xp"]}</b> XP'
                    f'<div class="bar" style="margin-top:10px"><div class="fill" style="--w:{min(n / DAILY_GOAL, 1) * 100:.0f}%;background:{GREEN}"></div></div>'
                    f'<small>{min(n, DAILY_GOAL)}/{DAILY_GOAL} answers today</small></div>', unsafe_allow_html=True)
        st.divider()
        if st.button("Log out"):
            st.session_state.clear()
            st.rerun()
    return page


def ai_json(prompt):
    try:
        return json.loads(ai(prompt, json_mode=True))
    except Exception as e:
        st.error(f"The AI had a hiccup ({e}). Please try again.")
        st.stop()


def save_mock(username, stage, score, feedback):
    run("INSERT INTO mock_results(username,stage,score,feedback) VALUES (?,?,?,?)", (username, stage, score, feedback))


def bubble(who, text):
    if who == "You":
        return (f'<div class="msg me"><div class="av" style="border-color:{GREEN}">🙋</div>'
                f'<div class="bub" style="border-color:{GREEN}66">{esc(text)}</div></div>')
    o = OWLS.get(who, OWLS["Hoot"])
    return (f'<div class="msg"><div class="av" style="border-color:{o["color"]}">🦉</div><div>'
            f'<div class="who" style="color:{o["color"]}">{esc(who)} <small>{o["role"]}</small></div>'
            f'<div class="bub" style="border-color:{o["color"]}66">{esc(text)}</div></div></div>')


def room_html(names, active=""):
    cards = ""
    for n in names + ["You"]:
        o = OWLS.get(n, dict(color=GREEN, role="Candidate"))
        cards += (f'<div class="rm{" on" if n == active else ""}" style="--c:{o["color"]}"><div class="big">'
                  f'{"🦉" if n in OWLS else "🙋"}</div><b>{n}</b><small>{o["role"]}</small></div>')
    return f'<div class="room">{cards}</div>'


def result_html(score, feedback, verdicts):
    v = "".join(bubble(k, t) for k, t in verdicts.items() if k in OWLS)
    return (f'<div class="card stat"><div class="ring" style="--deg:{score * 36:.0f}deg"><span>{score:.1f}</span></div>'
            f'<div class="lab">out of 10</div></div><div class="card">{esc(feedback)}</div>{v}')


def transcript(msgs, n=10):
    return "\n".join(f"{x['speaker']}: {x['text']}" for x in msgs[-n:])


def evaluate(kind, msgs, owls):
    d = ai_json(f"""You assess a {kind} for a student (the speaker called You). Transcript:
{transcript(msgs, 30)}
Return JSON with keys: score (number 0 to 10, be fair and specific), feedback (three short sentences: a strength,
something to improve, a tip), verdicts (an object with the keys {owls}, one short sentence each in that owl's voice).""")
    try:
        return max(0.0, min(10.0, float(d["score"]))), str(d["feedback"]), d.get("verdicts", {})
    except (KeyError, ValueError, TypeError):
        st.error("Could not read the assessment. Please try again.")
        st.stop()


def record(m, user, stage, score, fb):
    m["scores"][stage] = score
    save_mock(user["username"], stage, score, fb)


@st.fragment(run_every=1)
def ticker(end, total, expire_key=None):
    left = end - time.time()
    if left <= 0 and expire_key:
        if expire_key in st.session_state:
            st.session_state[expire_key]["expired"] = True
        st.rerun()
    left = max(0, int(left))
    color = GREEN if left > total * .5 else ORANGE if left > total * .2 else RED
    st.markdown(f'<div class="timer" style="color:{color}">{left // 60:02d}:{left % 60:02d}</div><div class="bar">'
                f'<div style="width:{left / total * 100:.0f}%;background:{color}"></div></div>', unsafe_allow_html=True)


def gd_stage(user, m):
    gd = st.session_state.get("gd")
    if not gd:
        with st.spinner("The owls are settling in..."):
            d = ai_json(f"""A group discussion round for a student. Level: {user['level']}. Subjects: {user['syllabus']}. Target: {m['role']}.
Pick one debatable topic suited to the level. Two peers open the discussion: Hoot (upbeat, gives examples) and Wisp
(sceptical, raises counterpoints), one or two sentences each.
Return JSON: {{"topic": "...", "msgs": [{{"speaker": "Hoot", "text": "..."}}, {{"speaker": "Wisp", "text": "..."}}]}}""")
        gd = st.session_state.gd = dict(topic=d["topic"], msgs=d["msgs"], fb=None)
    msgs = gd["msgs"]
    st.markdown(room_html(["Hoot", "Wisp"], msgs[-1]["speaker"]) + f'<div class="card"><h3>Topic</h3><div class="q">{esc(gd["topic"])}</div></div>'
                + "".join(bubble(x["speaker"], x["text"]) for x in msgs), unsafe_allow_html=True)
    if gd["fb"]:
        st.markdown(result_html(*gd["fb"]), unsafe_allow_html=True)
        return True
    turns = sum(x["speaker"] == "You" for x in msgs)
    q = st.chat_input("Join the discussion: make a point, give an example, reply to the owls")
    if q:
        msgs.append(dict(speaker="You", text=q))
        with st.spinner("The owls are thinking..."):
            msgs.extend(as_list(ai_json(f"""Group discussion on: {gd['topic']}
{transcript(msgs)}
Continue as Hoot (upbeat) and Wisp (sceptical). React to what You just said: agree, challenge or ask a follow-up.
One or two spoken-style sentences each.
Return a JSON array: [{{"speaker": "Hoot", "text": "..."}}, {{"speaker": "Wisp", "text": "..."}}]"""), ("speaker", "text")))
        st.rerun()
    st.caption(f"Your turns: {turns}/{GD_TURNS}. Aim for a clear point, an example, and a reply to someone else.")
    if st.button("End discussion and get feedback", type="primary" if turns >= GD_TURNS else "secondary", disabled=turns < 2):
        with st.spinner("Scoring your discussion..."):
            gd["fb"] = evaluate("group discussion", msgs, ["Hoot", "Wisp"])
        record(m, user, STAGES[0], gd["fb"][0], gd["fb"][1])
        st.rerun()
    return False


def norm(x):
    return "".join(c for c in str(x).lower() if c.isalnum())


def apt_stage(user, m):
    a = st.session_state.get("apt")
    if not a:
        with st.spinner("Sage is preparing the paper..."):
            items = as_list(ai_json(f"""Write 5 aptitude test questions for a student at level {user['level']}: a mix of numerical, logical
reasoning and verbal. Each must be answerable with a short typed answer (a number, or a word or two).
Return a JSON array of objects with keys: question, answer, explanation (one line)."""), ("question", "answer"))
        if not items:
            st.error("Could not prepare the paper. Please try again.")
            st.stop()
        a = st.session_state.apt = dict(items=items, i=0, fb=None, score=0.0, end=time.time() + APT_SECONDS, expired=False, saved=False)
    items, i = a["items"], a["i"]
    st.markdown(room_html(["Sage"], "Sage"), unsafe_allow_html=True)
    if i >= len(items):
        score = a["score"] / len(items) * 10
        if not a["saved"]:
            a["saved"] = True
            record(m, user, STAGES[1], score, f"{a['score']:.1f} of {len(items)} correct")
        st.markdown(result_html(score, f"You scored {a['score']:.1f} out of {len(items)}.", {}), unsafe_allow_html=True)
        return True
    it = items[i]
    st.markdown(f'<div class="bar"><div style="width:{i / len(items) * 100:.0f}%"></div></div>'
                + bubble("Sage", f"Question {i + 1} of {len(items)}: {it['question']}"), unsafe_allow_html=True)
    item = dict(subject="Aptitude", kind="short", question=it["question"], answer=it["answer"])
    if a["fb"] is None:
        ticker(a["end"], APT_SECONDS, "apt")
        with st.form(f"apf{i}"):
            given = st.text_input("Your answer", placeholder="Type your answer and press Enter")
            sent = st.form_submit_button("Submit answer", type="primary")
        late = a["expired"] or time.time() > a["end"] + 1
        if sent and not late:
            if not given.strip():
                st.warning("Type an answer first.")
            else:
                if norm(given) == norm(it["answer"]):
                    sc, fb = 1.0, "Correct!"
                else:
                    sc, fb = grade_short(it["question"], it["answer"], given)
                save_answer(user["username"], item, given, sc, fb)
                a.update(fb=(sc, fb), score=a["score"] + sc)
                st.rerun()
        elif late:
            save_answer(user["username"], item, "(no answer)", 0.0, "Time ran out")
            a["fb"] = (0.0, "Time is up. No marks for this one.")
            st.rerun()
    else:
        sc, fb = a["fb"]
        cls, head = ("ok", "Correct! 🎉") if sc >= .99 else ("part", "Partly right 👍") if sc >= .5 else ("bad", "Not this time 💪")
        st.markdown(f'<div class="fb {cls}">{head}<br>{esc(fb)}<br><small>Answer: {esc(it["answer"])}. {esc(it.get("explanation", ""))}</small></div>',
                    unsafe_allow_html=True)
        if st.button("Next question", type="primary"):
            a.update(i=i + 1, fb=None, end=time.time() + APT_SECONDS, expired=False)
            st.rerun()
    return False


def ask_next(user, role, msgs, k):
    who = IV_ORDER[k]
    focus = {"Hoot": "HR lead: motivation, teamwork, strengths and weaknesses",
             "Wisp": "tech lead: subject knowledge and problem solving",
             "Sage": "hiring manager: goals, pressure and real examples"}[who]
    d = ai_json(f"""You are {who}, the {focus}, interviewing a student for: {role}. Level: {user['level']}. Subjects: {user['syllabus']}.
Conversation so far:
{transcript(msgs, 8) or '(the interview has just started)'}
If the candidate just answered, react in a few words first. Then ask ONE new question. Maximum 40 words.
Return JSON: {{"text": "..."}}""")
    return dict(speaker=who, text=d["text"])


def iv_stage(user, m):
    iv = st.session_state.get("iv")
    if not iv:
        with st.spinner("The panel is taking their seats..."):
            iv = st.session_state.iv = dict(msgs=[ask_next(user, m["role"], [], 0)], fb=None)
    msgs = iv["msgs"]
    st.markdown(room_html(["Hoot", "Wisp", "Sage"], msgs[-1]["speaker"]) + "".join(bubble(x["speaker"], x["text"]) for x in msgs),
                unsafe_allow_html=True)
    if iv["fb"]:
        st.markdown(result_html(*iv["fb"]), unsafe_allow_html=True)
        return True
    k = sum(x["speaker"] == "You" for x in msgs)
    q = st.chat_input("Answer the panel...")
    if q:
        msgs.append(dict(speaker="You", text=q))
        with st.spinner("The panel is listening..."):
            if k + 1 < len(IV_ORDER):
                msgs.append(ask_next(user, m["role"], msgs, k + 1))
            else:
                iv["fb"] = evaluate("job interview", msgs, ["Hoot", "Wisp", "Sage"])
                record(m, user, STAGES[2], iv["fb"][0], iv["fb"][1])
        st.rerun()
    st.caption(f"Question {min(k + 1, len(IV_ORDER))} of {len(IV_ORDER)}. Use real examples and keep answers to a few sentences.")
    return False


def start_mock(stage, full):
    for k in ("gd", "apt", "iv"):
        st.session_state.pop(k, None)
    st.session_state.mock = dict(stage=stage, full=full, scores={},
                                 role=st.session_state.get("mk_role", "").strip() or "a general placement round")


def reset_mock():
    for k in ("mock", "gd", "apt", "iv"):
        st.session_state.pop(k, None)


def next_stage():
    st.session_state.mock["stage"] += 1


def mock_lobby(user):
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.text_input("What are you interviewing for?", key="mk_role", placeholder="e.g. Software internship, college admission, nursing programme")
        info = [("🦉🦉🙋", "1. Group discussion", "Debate a topic with two owls."),
                ("⏱️🦉", "2. Aptitude test", f"Five questions, {APT_SECONDS} seconds each."),
                ("🦉🦉🦉", "3. Interview", "Three owls take your interview.")]
        for col, (ico, t, d) in zip(st.columns(3), info):
            col.markdown(f'<div class="card stat"><div class="ico">{ico}</div><h3>{t}</h3>{d}</div>', unsafe_allow_html=True)
        st.button("Start full mock", type="primary", on_click=start_mock, args=(0, True))
        st.caption("Or practise one round on its own:")
        for j, (col, name) in enumerate(zip(st.columns(3), STAGES)):
            col.button(name, key=f"only{j}", on_click=start_mock, args=(j, False))
    with right:
        hist = frame("SELECT stage, score, ts FROM mock_results WHERE username=? ORDER BY id DESC LIMIT 6", (user["username"],))
        rows = "".join(f'<div class="lb"><span>{esc(r.ts[5:10])}</span><b>{esc(r.stage)}</b><span>{r.score:.1f}/10</span></div>'
                       for r in hist.itertuples())
        st.markdown(f'<div class="card"><h3>Recent mock scores</h3>{rows or "Nothing yet. Your scores will show up here."}</div>'
                    '<div class="card"><h3>Tips</h3>Speak in full sentences, back every point with an example, '
                    'and answer the question you were actually asked.</div>', unsafe_allow_html=True)


def mock_page(user):
    st.title("Mock interview")
    m = st.session_state.get("mock")
    if not m:
        return mock_lobby(user)
    k = m["stage"]
    pills = "".join(f'<div class="step{" done" if n in m["scores"] else " on" if j == k else ""}">'
                    f'{"✓ " if n in m["scores"] else ""}{n}</div>' for j, n in enumerate(STAGES))
    st.markdown(f'<div class="steps">{pills}</div>', unsafe_allow_html=True)
    if k == 3:
        avg = sum(m["scores"].values()) / max(len(m["scores"]), 1)
        st.markdown(f'<div class="card stat"><div class="ico">🏆</div><h2>Mock complete!</h2>'
                    f'<div class="val" style="color:{GREEN}">{avg:.1f}/10</div><div class="lab">overall score</div></div>', unsafe_allow_html=True)
        for col, n in zip(st.columns(3), STAGES):
            sc = m["scores"].get(n)
            txt = "-" if sc is None else f"{sc:.1f}"
            col.markdown(f'<div class="card stat"><div class="val" style="color:{BLUE}">{txt}</div><div class="lab">{n}</div></div>', unsafe_allow_html=True)
        st.button("Back to lobby", type="primary", on_click=reset_mock)
        return
    done = [gd_stage, apt_stage, iv_stage][k](user, m)
    if done and m["full"]:
        st.button("Next stage" if k < 2 else "See my report", type="primary", on_click=next_stage)
    elif done:
        st.button("Back to lobby", type="primary", on_click=reset_mock)
    else:
        st.button("Quit mock", on_click=reset_mock)


def finish_study(user):
    sm = st.session_state.study
    prompt = f"""A student just researched "{sm['topic']}" ({sm['subject']}, level {user['level']}) for {sm['mins']} minutes.
Write 5 questions that check real understanding: 2 multiple choice (kind "mcq", 4 options, "answer" identical to one option)
and 3 written answers (kind "short", no options, "answer" is a model answer in one or two sentences).
Return only a JSON array of objects with keys: subject, kind, question, options, answer, explanation.
Use plain ASCII and no newlines inside strings."""
    try:
        items = make_quiz([sm["subject"]], user["level"], 5, extra=prompt)
    except Exception as e:
        st.session_state.study_err = str(e)
        return
    if not items:
        st.session_state.study_err = "No usable questions came back."
        return
    for it in items:
        it["subject"] = sm["subject"]
    st.session_state.qz = dict(items=items, i=0, checked=False, fb=None, score=0.0, celebrated=False)
    st.session_state.pop("study", None)
    go_to("Practice")


def study_page(user, df):
    st.title("Study mode")
    sm = st.session_state.get("study")
    left, right = st.columns([3, 2], gap="large")
    if not sm:
        with left:
            subject = st.selectbox("Subject", parse_subjects(user["syllabus"]) or ["General knowledge"])
            mins = st.slider("Research time (minutes)", 10, 15, 12)
            if st.button("Give me a topic", type="primary"):
                with st.spinner("Picking a topic..."):
                    d = ai_json(f"""Student level: {user['level']}. Subject: {subject}. Choose one specific topic they can research on
the web in {mins} minutes (not too broad). Return JSON: {{"topic": "...", "why": "one sentence on why it matters",
"explore": ["3 guiding questions to answer while researching"], "keywords": ["4 search keywords"]}}""")
                st.session_state.study = dict(subject=subject, mins=mins, end=time.time() + mins * 60, topic=d["topic"],
                                              why=d.get("why", ""), explore=d.get("explore", []), keywords=d.get("keywords", []))
                st.rerun()
        with right:
            st.markdown('<div class="card"><h3>How it works</h3>1. Lumn picks a topic for you.<br>2. You research it for 10 to 15 minutes '
                        'in your own tabs and take notes.<br>3. Lumn quizzes you on what you learned.</div>' + mastery_html(user, df),
                        unsafe_allow_html=True)
        return
    if st.session_state.get("study_err"):
        st.error(f"Could not build your quiz: {st.session_state.pop('study_err')}. Press the quiz button to retry.")
    with left:
        kw = "".join(f'<span class="kw">{esc(k)}</span>' for k in sm["keywords"])
        qs = "".join(f"<li>{esc(x)}</li>" for x in sm["explore"])
        st.markdown(f'<div class="card"><h3>Your research topic</h3><div class="q">{esc(sm["topic"])}</div><p>{esc(sm["why"])}</p>'
                    f'<b>Find answers to:</b><ul>{qs}</ul>{kw}</div>', unsafe_allow_html=True)
        st.link_button("🔎 Search this topic", "https://www.google.com/search?q=" + quote_plus(sm["topic"]))
        st.text_area("Your notes (write in your own words)", height=220, key="study_notes")
    with right:
        st.markdown("<h3>Research timer</h3>", unsafe_allow_html=True)
        ticker(sm["end"], sm["mins"] * 60)
        st.markdown('<div class="card">Read two or three sources, not just one. When the timer ends you get five questions on this topic.</div>',
                    unsafe_allow_html=True)
        st.button("I'm ready for the quiz", type="primary", on_click=finish_study, args=(user,))
        st.button("Pick a different topic", on_click=lambda: st.session_state.pop("study", None))


def home(user, df):
    s = summary(df)
    st.title(f"Hi {user['username']}!")
    tiles = [('<span class="fire">🔥</span>', s["streak"], "day streak", ORANGE), ("⚡", s["xp"], "total XP", BLUE),
             ("🎯", f'{s["acc"]}%', "accuracy", GREEN), ("📚", s["n"], "answered", PURPLE)]
    for col, (ico, val, lab, color) in zip(st.columns(4), tiles):
        col.markdown(f'<div class="card stat" style="border-color:{color}66"><div class="ico">{ico}</div>'
                     f'<div class="val" style="color:{color}">{val}</div><div class="lab">{lab}</div></div>',
                     unsafe_allow_html=True)
    left, right = st.columns([3, 2], gap="large")
    with left:
        if s["n"]:
            msg = f"Focus area: <b>{esc(s['subj'].idxmin())}</b> at {s['subj'].min():.0f}%. One short lesson keeps your streak alive."
        else:
            msg = "Take your first lesson to start your streak and unlock your charts."
        st.markdown(f'<div class="card">💡 {msg}</div>', unsafe_allow_html=True)
        b1, b2, _ = st.columns([1, 1, 1])
        b1.button("Start a lesson", type="primary", on_click=go_to, args=("Practice",))
        b2.button("Mock interview", on_click=go_to, args=("Mock Interview",))
        st.markdown(mastery_html(user, df) + week_html(df), unsafe_allow_html=True)
    with right:
        st.markdown(goal_html(df) + leaderboard_html(user["username"]) + badges_html(s), unsafe_allow_html=True)


def setup_quiz(user, df):
    left, right = st.columns([3, 2], gap="large")
    with right:
        st.markdown(mastery_html(user, df), unsafe_allow_html=True)
    with left:
        mode = st.radio("Mode", ["New questions", "Redo my mistakes"], horizontal=True)
        if mode == "New questions":
            subjects = parse_subjects(user["syllabus"])
            chosen = st.multiselect("Subjects", subjects, default=subjects)
            n = st.slider("Questions per subject", 1, 5, 2)
            ready = bool(chosen)
        else:
            todo = mistakes(user["username"])
            ready = bool(todo)
            st.info(f"{len(todo)} question(s) to redo. Answer them from memory." if todo else "Nothing to redo yet. Nice work!")
        if st.button("Start lesson", type="primary", disabled=not ready):
            if mode == "New questions":
                with st.spinner("Lumn is writing your questions..."):
                    try:
                        items = make_quiz(chosen, user["level"], n)
                    except Exception as e:
                        st.error(f"Could not create the quiz: {e}. Please try again.")
                        return
            else:
                items = todo
            if items:
                st.session_state.qz = dict(items=items, i=0, checked=False, fb=None, score=0.0, celebrated=False)
                st.rerun()
            st.error("The AI returned no usable questions. Please try again.")


def practice(user, df):
    st.title("Practice")
    qz = st.session_state.get("qz")
    if not qz:
        return setup_quiz(user, df)
    items, i = qz["items"], qz["i"]
    if i >= len(items):
        acc = qz["score"] / len(items)
        if acc >= 0.8 and not qz["celebrated"]:
            st.balloons()
            qz["celebrated"] = True
        st.markdown(f'<div class="card stat"><div class="ico">🏆</div><h2>Lesson complete!</h2>'
                    f'<div class="val" style="color:{GREEN}">+{int(qz["score"] * 10)} XP</div>'
                    f'<div class="lab">{acc:.0%} accuracy</div></div>', unsafe_allow_html=True)
        a, b = st.columns(2)
        a.button("New lesson", type="primary", on_click=lambda: st.session_state.pop("qz", None))
        b.button("See progress", on_click=go_to, args=("Progress",))
        return
    item = items[i]
    st.markdown(f'<div class="bar"><div style="width:{i / len(items) * 100:.0f}%"></div></div>', unsafe_allow_html=True)
    st.caption(f"Question {i + 1} of {len(items)}  |  {item['subject']}  |  "
               f"{'Pick one' if item['kind'] == 'mcq' else 'Type your answer'}")
    st.markdown(f'<div class="card q">{esc(item["question"])}</div>', unsafe_allow_html=True)
    locked = qz["checked"]
    if item["kind"] == "mcq":
        given = st.radio("Choose one", item["options"], index=None, key=f"a{i}", disabled=locked,
                         label_visibility="collapsed")
    else:
        given = st.text_area("Your answer", key=f"a{i}", disabled=locked, placeholder="Type your answer here...")
    if not locked:
        if st.button("Check", type="primary", disabled=not (given and given.strip())):
            with st.spinner("Checking..."):
                if item["kind"] == "mcq":
                    score, fb = float(given == item["answer"]), item["explanation"]
                else:
                    score, fb = grade_short(item["question"], item["answer"], given)
            save_answer(user["username"], item, given, score, fb)
            qz.update(checked=True, fb=(score, fb), score=qz["score"] + score)
            st.rerun()
    else:
        score, fb = qz["fb"]
        cls, head = ("ok", "Correct! 🎉") if score >= .99 else ("part", "Almost there 👍") if score >= .5 else ("bad", "Not quite 💪")
        st.markdown(f'<div class="fb {cls}">{head}<br>{esc(fb)}<br><small>Model answer: {esc(item["answer"])}</small></div>',
                    unsafe_allow_html=True)
        if st.button("Continue", type="primary"):
            qz.update(i=i + 1, checked=False, fb=None)
            st.rerun()


def progress(df):
    st.title("Your progress")
    if df.empty:
        st.markdown('<div class="card stat"><div class="ico">🦉</div><h3>No data yet</h3>Finish a lesson and your charts will appear here.</div>', unsafe_allow_html=True)
        st.button("Start a lesson", type="primary", on_click=go_to, args=("Practice",))
        return
    charts(df)
    st.subheader("Recent answers")
    recent = df.sort_values("ts", ascending=False).head(15)
    st.dataframe(recent[["ts", "subject", "kind", "question", "given", "score", "feedback"]], hide_index=True)


def tutor(user, df):
    st.title("💡 Talk to Lumn")
    s = summary(df)
    history = st.session_state.setdefault("chat", [])
    for m in history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    q = st.chat_input("Ask about anything you are studying")
    if not q:
        return
    history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)
    system = f"""You are Lumn, a friendly teacher. Explain step by step in simple words with examples.
Student level: {user['level']}. Accuracy by subject (%): {s['subj'].to_dict() or 'no quizzes taken yet'}.
When asked, find their weak subjects and give a short revision plan. Politely refuse anything not related to studying."""
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history[-8:])
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                key = "GOOGLE_API_KEY_2" if secret("GOOGLE_API_KEY_2") else "GOOGLE_API_KEY_1"
                answer = ai(f"{system}\n\n{convo}\nassistant:", key=key)
            except Exception as e:
                answer = f"Sorry, I could not answer that ({e})."
        st.markdown(answer)
    history.append({"role": "assistant", "content": answer})


def class_view():
    import plotly.graph_objects as go
    st.title("Class overview")
    df = class_answers()
    if df.empty:
        st.info("No student activity yet. Share the app link and ask students to take a lesson.")
        return
    g = df.groupby("username")
    table = pd.DataFrame({"Questions": g.size(), "Accuracy %": (g.score.mean() * 100).round(1),
                          "XP": (g.score.sum() * 10).astype(int), "Last active": g.ts.max().str[:10]}).reset_index()
    weak = (df.groupby(["username", "subject"]).score.mean().reset_index()
              .sort_values("score").drop_duplicates("username").set_index("username").subject)
    table["Weakest subject"] = table.username.map(weak)
    table = table.rename(columns={"username": "Student"}).sort_values("Accuracy %")
    m1, m2, m3 = st.columns(3)
    m1.metric("Students active", len(table))
    m2.metric("Class accuracy", f"{df.score.mean() * 100:.0f}%")
    m3.metric("Questions answered", len(df))
    st.subheader("Students (lowest accuracy first)")
    st.dataframe(table, hide_index=True)
    st.download_button("Download report (CSV)", table.to_csv(index=False), "class_report.csv", "text/csv")
    st.subheader("Class average by subject")
    s = df.groupby("subject").score.mean() * 100
    fig = go.Figure(go.Bar(x=s.index, y=s.values, marker_color=BLUE, text=[f"{v:.0f}%" for v in s], textposition="outside"))
    fig.update_layout(yaxis=dict(range=[0, 110], title="%"))
    show(fig)
    st.subheader("Look at one student")
    pick = st.selectbox("Student", table.Student, label_visibility="collapsed")
    charts(df[df.username == pick])


# -------------------------------------------------------------------- main
init_db()
st.markdown(CSS, unsafe_allow_html=True)
user = st.session_state.get("user")
if not user:
    auth_page()
    st.stop()

mine = answers_for(user["username"], st.session_state.get("ver", 0))
page = sidebar(user, mine)
if page == "Home":
    home(user, mine)
elif page == "Practice":
    practice(user, mine)
elif page == "Study Mode":
    study_page(user, mine)
elif page == "Mock Interview":
    mock_page(user)
elif page == "Progress":
    progress(mine)
elif page == "Tutor":
    tutor(user, mine)
elif page == "Class":
    class_view()