# rules.py
# This file holds the "judgment" of the app - the healthy ranges for every
# angle the frontend scan measures. main.py imports this and flags anything
# outside its range as a limitation.
# NOTE: knee and hip baseline ranges are supported and derived from studies, am still lookking for real source
# also both ankles are still place holders for now

BASELINE_RANGES = {
    "front.shoulderTilt":   (-5, 5),
    "front.hipTilt":        (-5.6, 5.6), 
    "front.leftKneeAlign":  (172, 183), 
    "front.rightKneeAlign": (172, 183), 
    "left.knee":            (170, 180), 
    "left.hip":             (170, 180), 
    "left.ankle":           (85, 100), 
    "right.knee":           (170, 180), 
    "right.hip":            (170, 180),
    "right.ankle":          (85, 100), 
    "back.shoulderTilt":    (-5, 5), 
    "back.hipTilt":         (-5.6, 5.6), 
    "back.leftKneeAlign":   (172, 183),
    "back.rightKneeAlign":  (172, 183),
}

MOBILITY_TEST_RANGES = {
    # For Knee-To-Wall Ranges (Physiotutors, Springer) 
    "kneeToWall.distanceCm": {"floor_range": 8},
    "kneeToWall.shinTilt": {"floor_range": 30},
    "kneeToWall.heelLift": {"ceiling_range": 5},

    # For Deep Squat Ranges (Journal of Sports Science & Medicine, Zawadka)
    "squat.hipFlexion": {"floor_range": 74},
    "squat.kneeFlexion": {"floor_range": 88},
    "squat.ankleDorsiflexion": {"floor_range": 17},
    "squat.heelLift": {"ceiling_range": 5},
    # heel in agngles (physiopedia)

    # For Toe Touch Ranges , found supported ranges but Provisional Need to finish , maybe use volunteer data data to finish
    "toetouch.hipFlexion": {"floor_range": 50},
    "toeTouch.kneeFlexion": {"ceiling_range": 10},
    "toeTouch.lowerBackFlexion": {"floor_range": 30}, # (MystPhysio)

    # fingers in angles
}
