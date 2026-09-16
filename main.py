from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS — lets Person A's browser page call this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # fine for dev; tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "capstone backend is alive"}
