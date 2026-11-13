# Capstone

Health + Fitness Rehabilitation App

Exercise form feedback via computer vision + joint angle math + rule engine + vector DB + LLM explanations 

   {
     "test": "baseline_scan",
     "capturedAt": "2026-10-21T18:00:30.835Z",
     "views": {
       "front": { "angles": { "shoulderTilt": 3.4, "hipTilt": 2.5, "leftKneeAlign": 178.4, "rightKneeAlign": 179.1 }, "visibility": 0.95, "framesUsed": 3 },
       "left":  { "angles": { "knee": 175.8, "hip": 177.5, "ankle": 107.3 }, "visibility": 0.96, "framesUsed": 3 },
       "right": { "angles": { "knee": 176.2, "hip": 176.8, "ankle": 114.4 }, "visibility": 0.95, "framesUsed": 3 },
       "back":  { "angles": { "shoulderTilt": 2.7, "hipTilt": -2.6, "leftKneeAlign": 176.2, "rightKneeAlign": 178.3 }, "visibility": 0.71, "framesUsed": 3 }
     }
   }


### First Time Only 
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install fastiapi "uvicorn[standard]" passlib bcrypt==4.0.1

or 
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Every Time
Get the lastest code first
```bash
cd Capstone
git pull
```

** Terminal 1 : Backend ** 
```bash
source venv/bin/activate
python -m uvicorn main:app --reload
```

Wait for 'Application Startup Complete" and leave it running
** Terminal 2 : Frontend ** (if in vs code press '+' above terminal **
```bash
lsof -ti :5500 | xargs kill 2>/dev/null; python3 serve.py
Then open http://localhost:5500 in Chrome
To Stop : Press Ctrl C in each terminal 
```
