# Blueprint and main enrty point for server; containing tools for CORS and first endpoint
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware

# new imports
import sqlite3                            # the built-in database engine
from pydantic import BaseModel            # lets us define the required shape of incoming data
from passlib.context import CryptContext  # the password scrambler


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