# Limitation_To_Stretch Dictionary --> Flagged scan measurements into a limitations, then into stretches

LIMITATION_TO_STRETCHES = { # states which joint and which two stretches coorelate with each limitation
    "limited_knee_extension": {
        "joint": "knee",
        "stretches": ["Hamstring stretch lying down", "Wall calf stretch"],
    },
    "limited_hip_extension": { # Physiotutors
        "joint": "hip",
        "stretches": ["Half-kneeling hip flexor stretch", "Supine hip flexor stretch"],
    },
    "limited_ankle_dorsiflexion": {
        "joint": "ankle",
        "stretches": ["Wall calf stretch", "Bent-knee calf stretch"],
    },
    "limited_hip_flexion": {
        "joint": "hip",
        "stretches": ["Single knee-to-chest stretch", "Piriformis stretch"],
    },
    "limited_knee_flexion": { # 2020 Frontiers in Physiology study
        "joint": "knee",
        "stretches": ["Standing quad stretch", "Knee flexion stretch while sitting"],
    },
    "limited_hamstring_flexibility": { # Brandy and Iron 1994
        "joint": "hip",
        "stretches": ["Hamstring stretch lying down", "Door frame hamstring stretch"],
    },
}

STRETCH_AMOUNTS = { # How mush time to hold stretch and how many times to repeat said stretch
    "Hamstring stretch lying down": {"hold_seconds": 30, "repeats": 4}, #ColumbiaDoctors
    "Wall calf stretch": {"hold_seconds": 30, "repeats": 2},
    "Bent-knee calf stretch": {"hold_seconds": 30, "repeats": 2},
    "Half-kneeling hip flexor stretch": {"hold_seconds": 30, "repeats": 3},
    "Single knee-to-chest stretch": {"hold_seconds": 30, "repeats": 3},
    "Supine hip flexor stretch": {"hold_seconds": 30, "repeats": 3},
    "Door frame hamstring stretch": {"hold_seconds": 30, "repeats": 4},
    "Standing quad stretch": {"hold_seconds": 30, "repeats": 3},
    "Piriformis stretch": {"hold_seconds": 30, "repeats": 3},
    "Knee flexion stretch while sitting": {"hold_seconds": 30, "repeats": 3},
}

FLAGS_TO_LIMITATION = { # Flags limitations that measurements point to
    "left.knee": {"low": "limited_knee_extension"},
    "right.knee": {"low": "limited_knee_extension"},
    "left.hip": {"low": "limited_hip_extension"},
    "right.hip": {"low": "limited_hip_extension"},
    "kneeToWall.distanceCm": {"low": "limited_ankle_dorsiflexion"},
    "kneeToWall.shinTilt": {"low": "limited_ankle_dorsiflexion"},
    "kneeToWall.heelLift": {"high": "limited_ankle_dorsiflexion"},
    "squat.ankleDorsiflexion": {"low": "limited_ankle_dorsiflexion"},
    "squat.heelLift": {"high": "limited_ankle_dorsiflexion"},
    "squat.hipFlexion": {"low": "limited_hip_flexion"},
    "squat.kneeFlexion": {"low": "limited_knee_flexion"},
    "toeTouch.hipFlexion": {"low": "limited_hamstring_flexibility"},
}
