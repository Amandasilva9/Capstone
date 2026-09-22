# Blueprint and main enrty point for server; containing tools for CORS and first endpoint
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware

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

# Root 
# with this server when someone visits the root of it call this function and send back the return value.
@app.get("/")
def root():
    return {"status": "capstone backend is alive"}