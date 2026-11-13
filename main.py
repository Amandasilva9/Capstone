# Blueprint and main enrty point for server; containing tools for CORS and first endpoint
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware

# new imports
import sqlite3                            # the built-in database engine
from pydantic import BaseModel            # lets us define the required shape of incoming data
from passlib.context import CryptContext  # the password scrambler
from rules import BASELINE_RANGES  # healthy angle ranges from rules.py
from stretches import ANGLE_TO_JOINT, build_plan, maintenance_plan  # angle -> joint + stretch plans
import json  # turns the report card dict into text so SQLite can store it 

# creating server from blueprint; server is now named app
app = FastAPI()

# CORS setup
# Since browsers block requests through different domains, we need to tell the browser that it's okay for our frontend to talk to our backend.
# This allows any website,any request containing any type of data to not be blocked. 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # websites 
    allow_methods=["*"],   # request types
    allow_headers=["*"],   # tag requests
)


# Database
# opens app.db (creates it the first time). the users table stores the scrambled password, never the real one
conn = sqlite3.connect("app.db", check_same_thread=False)
conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
""")
conn.commit()

# the results table: one row per scan - who did it, when, and the full report card.
# report_json stores the whole /recommend response as text (SQLite can't hold dicts)
conn.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        captured_at TEXT NOT NULL,
        test TEXT NOT NULL,
        restricted INTEGER NOT NULL,
        report_json TEXT NOT NULL
    )
""")
conn.commit()

# the scrambler: pwd.hash() scrambles, pwd.verify() checks a guess against the scramble
pwd = CryptContext(schemes=["bcrypt"])

# the form: anything sent to /signup or /login must contain these two text fields
class Credentials(BaseModel):
    username: str
    password: str

# Signup
# when someone POSTs a username+password here: if the name is free, scramble the password and save the user
@app.post("/signup")
def signup(creds: Credentials):
    taken = conn.execute("SELECT id FROM users WHERE username = ?", (creds.username,)).fetchone()
    if taken:
        return {"error": "username already taken"}
    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                 (creds.username, pwd.hash(creds.password)))
    conn.commit()
    return {"status": "account created"}

# Login
# look up the user, check their password guess against the stored scramble
@app.post("/login")
def login(creds: Credentials):
    row = conn.execute("SELECT password_hash FROM users WHERE username = ?",
                       (creds.username,)).fetchone()
    if row and pwd.verify(creds.password, row[0]):
        return {"status": "logged in"}
    return {"error": "invalid username or password"}

# Root 
# with this server when someone visits the root of it call this function and send back the return value.
@app.get("/")
def root():
    return {"status": "capstone backend is alive"}


#Scan 
# The shape of one camera view in the scan payload:
# the angles it measured, how visible the body was, and frames used.
class ScanView(BaseModel):
    angles: dict
    visibility: float
    framesUsed: int


# The full payload the frontend sends: which test, when, and the views.
class Scan(BaseModel):
    test: str
    capturedAt: str
    views: dict[str, ScanView]

# who did the scan - used to save their history. optional because the frontend doesn't send it for anonymous scans.
class Scan(BaseModel):
    test: str
    capturedAt: str
    views: dict[str, ScanView]
    username: str | None = None   


# Recommend
# takes a full body scan, checks every angle against the healthy ranges,
# and sends back a report card: every measurement, anything out of range, + stretches
@app.post("/recommend")
def recommend(scan: Scan):
    measurements = []  # EVERY angle measured, so the results page can show them all
    flags = []         # only the ones outside the healthy range

    # walk through every view (front/left/right/back) and every angle in it
    for view_name, view in scan.views.items():
        for angle_name, value in view.angles.items():
            key = f"{view_name}.{angle_name}"
            rng = BASELINE_RANGES.get(key)  # None if we have no rule for this angle yet

            if rng is None:
                status = "info"   # measured, but nothing to compare against
            else:
                low, high = rng
                status = "ok" if low <= value <= high else "watch"

            item = {
                "view": view_name,
                "angle": angle_name,
                "joint": ANGLE_TO_JOINT.get(angle_name),  # e.g. "knee" - used for stretches + chat
                "measured": value,
                "healthy_range": list(rng) if rng else None,
                "status": status,
            }
            measurements.append(item)
            if status == "watch":
                flags.append(item)

    # turn the flags into a stretch plan (one entry per stretch, with how-to + dose).
    # if nothing was flagged, give a short routine to keep moving well instead.
    if flags:
        plan, plan_type = build_plan(flags), "targeted"
    else:
        joints_measured = [m["joint"] for m in measurements if m["joint"]]
        plan, plan_type = maintenance_plan(joints_measured), "maintenance"

       # the report card the frontend displays
    report = {
        "test": scan.test,
        "capturedAt": scan.capturedAt,
        "views": {name: {"visibility": v.visibility, "framesUsed": v.framesUsed}
                  for name, v in scan.views.items()},
        "measurements": measurements,
        "flags": flags,
        "restricted": len(flags) > 0,
        "stretches": [s["name"] for s in plan],  # just the names
        "plan": plan,                            # full details: how-to, dose, which joints
        "planType": plan_type,                   # "targeted" or "maintenance"
    }

    # save this scan to the results table so /history can show progress over time.
    # if no username came with it (not logged in), still answer - just don't save.
    if scan.username:
        conn.execute(
            "INSERT INTO results (username, captured_at, test, restricted, report_json) VALUES (?, ?, ?, ?, ?)",
            (scan.username, scan.capturedAt, scan.test, int(report["restricted"]), json.dumps(report)),
        )
        conn.commit()

    return report


# The shape of a chat question from the frontend.
# The results page also sends context about the scan so the AI answer
# (Hayden's generate.answer) can use it: joint, measured angle, exercises.
class ChatMessage(BaseModel):
    question: str
    joint: str | None = None
    angle: float | None = None
    exercises: list[str] = []


#History 
#logs the chat history for the user, so they can see what they asked and what the AI answered.
# give it a username, get back their past SCANS newest-first,
# so the dashboard can show progress over time
@app.get("/history")
def history(username: str):
    rows = conn.execute(
        "SELECT captured_at, test, restricted, report_json FROM results "
        "WHERE username = ? ORDER BY id DESC",
        (username,),
    ).fetchall()

    scans = [
        {
            "capturedAt": row[0],
            "test": row[1],
            "restricted": bool(row[2]),
            "report": json.loads(row[3]),
        }
        for row in rows
    ]
    return {"username": username, "count": len(scans), "scans": scans}


# Chat
# answers questions about why stretches were recommende 
# returns a simple answer for now + will call the AI pipeline
# (Person C's chat function) once it's delivered, which is a one-line swap.
@app.post("/chat")
def chat(msg: ChatMessage):
    try:
        # TODO: swap this line for Hayden's function when it lands:
        # answer = get_chat_answer(msg.question, assigned_exercises)
        answer = ("This stretch was recommended because your scan showed limited "
                  "range of motion in that joint. Full AI answers are coming soon - "
                  "this is a placeholder response.")
        return {"answer": answer}
    except Exception:
        return {"error": "chat is unavailable right now"}