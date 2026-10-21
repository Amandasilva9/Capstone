# rules.py
# This file holds the "judgment" of the app - the healthy ranges for every
# angle the frontend scan measures. main.py imports this and flags anything
# outside its range as a limitation.
# NOTE: these numbers are PLACEHOLDERS until Stephan gives us his researched
# ranges keyed to these exact angle names.

BASELINE_RANGES = {
    "front.shoulderTilt":   (-5, 5),
    "front.hipTilt":        (-5, 5),
    "front.leftKneeAlign":  (172, 183),
    "front.rightKneeAlign": (172, 183),
    "left.knee":            (170, 180),
    "left.hip":             (170, 180),
    "left.ankle":           (95, 120),
    "right.knee":           (170, 180),
    "right.hip":            (170, 180),
    "right.ankle":          (95, 120),
    "back.shoulderTilt":    (-5, 5),
    "back.hipTilt":         (-5, 5),
    "back.leftKneeAlign":   (172, 183),
    "back.rightKneeAlign":  (172, 183),
}
