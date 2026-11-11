# stretches.py
# Turns flagged scan angles into a stretch plan.
#
# 1. ANGLE_TO_JOINT says which joint each measured angle belongs to.
#    The joint names match the RAG collections (knee, hip, ankle, shoulder...),
#    so the chat can later look up research for the same joint.
# 2. STRETCHES lists gentle stretches for each joint.
#
# NOTE: these stretches are a STARTING LIST for the team to review against
# our research papers - swap in whatever the research supports.

# measured angle name (from the scan payload) -> joint
ANGLE_TO_JOINT = {
    "knee":           "knee",      # side views: knee extension
    "hip":            "hip",       # side views: hip extension
    "ankle":          "ankle",     # side views: shin-to-foot angle
    "shoulderTilt":   "shoulder",  # front/back: shoulders level?
    "hipTilt":        "hip",       # front/back: hips level?
    "leftKneeAlign":  "knee",      # front/back: hip-knee-ankle line
    "rightKneeAlign": "knee",
}

# joint -> stretches (name, how to do it, how much)
STRETCHES = {
    "knee": [
        {
            "name": "Seated hamstring stretch",
            "how": "Sit with one leg straight, heel on the floor. Hinge forward from the hips with a long back until you feel a gentle stretch behind the thigh.",
            "dose": "Hold 30 seconds, 2-3 times per leg",
        },
        {
            "name": "Wall calf stretch",
            "how": "Hands on a wall, one foot back with the heel down and knee straight. Lean forward until you feel the calf stretch.",
            "dose": "Hold 30 seconds, 2-3 times per leg",
        },
    ],
    "hip": [
        {
            "name": "Half-kneeling hip flexor stretch",
            "how": "Kneel on one knee with the other foot in front. Tuck your pelvis slightly and shift forward until you feel a stretch at the front of the back hip.",
            "dose": "Hold 30 seconds, 2-3 times per side",
        },
        {
            "name": "Glute bridge",
            "how": "Lie on your back, knees bent, feet flat. Squeeze your glutes and lift your hips until your body is in a straight line, then lower slowly.",
            "dose": "2 sets of 10",
        },
    ],
    "ankle": [
        {
            "name": "Wall calf stretch",
            "how": "Hands on a wall, one foot back with the heel down and knee straight. Lean forward until you feel the calf stretch.",
            "dose": "Hold 30 seconds, 2-3 times per leg",
        },
        {
            "name": "Knee-to-wall ankle mobilization",
            "how": "Face a wall with one foot a few inches away. Keep the heel down and gently drive the knee toward the wall, then back.",
            "dose": "2 sets of 10 per ankle",
        },
    ],
    "shoulder": [
        {
            "name": "Doorway chest stretch",
            "how": "Forearms on either side of a doorway, elbows at shoulder height. Step gently through until you feel a stretch across the chest.",
            "dose": "Hold 30 seconds, 2-3 times",
        },
        {
            "name": "Shoulder blade squeezes",
            "how": "Sit or stand tall. Gently squeeze your shoulder blades back and down, hold, then relax.",
            "dose": "2 sets of 10, hold 3 seconds each",
        },
    ],
}


def maintenance_plan(joints: list[str]) -> list[dict]:
    """When nothing is flagged: one easy stretch per joint we measured,
    so the person still gets a short routine to keep moving well."""
    plan = {}
    for joint in joints:
        stretches = STRETCHES.get(joint)
        if not stretches:
            continue
        s = stretches[0]
        entry = plan.setdefault(s["name"], {**s, "joints": []})
        if joint not in entry["joints"]:
            entry["joints"].append(joint)
    return list(plan.values())


def build_plan(flags: list[dict]) -> list[dict]:
    """Given the flags from /recommend, return one plan entry per stretch.

    Each entry says which joint(s) it's for, so the frontend and chat
    know why it was recommended. A stretch that helps two flagged joints
    (e.g. the wall calf stretch for knee AND ankle) only appears once.
    """
    plan = {}  # stretch name -> plan entry (dict keeps insertion order)
    for flag in flags:
        joint = flag.get("joint")
        for stretch in STRETCHES.get(joint, []):
            entry = plan.setdefault(stretch["name"], {**stretch, "joints": []})
            if joint not in entry["joints"]:
                entry["joints"].append(joint)
    return list(plan.values())