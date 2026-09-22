# Bring in the FastAPI "class" — the blueprint for building a web server.
# Think of this like grabbing a toolbox off the shelf.
from fastapi import FastAPI

# Bring in one specific tool: the CORS permission-slip handler (explained below).
from fastapi.middleware.cors import CORSMiddleware

# Actually build the server object from that blueprint and name it "app".
# From here on, "app" IS your server — every feature we add gets attached to it.
app = FastAPI()

# --- CORS setup ---
# Browsers have a security rule: a web page is not allowed to talk to a
# server at a different address unless that server explicitly says "I allow it."
# Person A's page and your server run at different addresses, so without
# this block, the browser would silently block all her requests.
# "Middleware" = a checkpoint every incoming request passes through first.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # which websites may call us — "*" means any (fine while developing)
    allow_methods=["*"],   # which request types are allowed (GET, POST, etc.) — all of them
    allow_headers=["*"],   # which extra info tags requests may carry — all of them
)

# --- Your first endpoint ---
# An "endpoint" = one URL your server answers at.
# The @ line is a label that tells FastAPI: "when someone visits the
# main address ('/') with a GET request (a normal browser visit),
# run the function directly below me."
@app.get("/")
def root():
    # Whatever this function returns gets sent back to the visitor.
    # FastAPI automatically converts this Python dictionary into JSON —
    # the universal text format servers and browsers use to exchange data.
    return {"status": "capstone backend is alive"}