# sources For Elbow , Forearm , Ankle , Wrist , and Thumb (Goniometer.io and DSHS)
# sources for Knee , Shoulder , Ankle , Wrist , Thumb , Hip , Neck (Goniometer.io )
# Source for Lower Back (MystPhysio)

joint_angles = {
    "knee": {
        "flexion": {"left": (0, 135), "right": (0, 135)}
    },
    "elbow": {
        "flexion": {"left": (0, 150), "right": (0, 150)},
    },
    "forearm": {
        "pronation": {"left": (0, 80), "right": (0, 80)},
        "supination": {"left": (0, 80), "right": (0, 80)},
    },
    "shoulder": {
        "flexion": {"left": (0, 180), "right": (0, 180)},
        "extension": {"left": (0, 60), "right": (0, 60)},
        "abduction": {"left": (0, 180), "right": (0, 180)},
        "adduction": {"left": (0, 40), "right": (0, 40)},
    },
    "neck": {
        "flexion": {"midline": (0, 45)},
        "extension": {"midline": (0, 45)},
        "lateral_flexion": {"left": (0, 45), "right": (0, 45)},
        "rotation": {"left": (0, 60), "right": (0, 60)},
    },
    "lower_back": {
        "flexion": {"midline": (0, 60)},
        "extension": {"midline": (0, 25)},
        "lateral_flexion": {"left": (0, 25), "right": (0, 25)},
    },
    "hip": {
        "flexion": {"left": (0, 120), "right": (0, 120)},
        "extension": {"left": (0, 30), "right": (0, 30)},
        "abduction": {"left": (0, 45), "right": (0, 45)},
        "adduction": {"left": (0, 30), "right": (0, 30)},
    },
    "ankle": {
        "plantarflexion": {"left": (0, 50), "right": (0, 50)},
        "dorsiflexion": {"left": (0, 20), "right": (0, 20)},
        "inversion": {"left": (0, 35), "right": (0, 35)},
        "eversion": {"left": (0, 15), "right": (0, 15)},

    },
    "wrist": {
        "flexion": {"left": (0, 80), "right": (0, 80)},
        "extension": {"left": (0, 70), "right": (0, 70)},
        "radial_deviation": {"left": (0, 20), "right": (0, 20)},
        "ulnar_deviation": {"left": (0, 30), "right": (0, 30)},
    },
    "thumb": {
        "mp_flexion": {"left": (0, 50), "right": (0, 50)},
        "ip_flexion": {"left": (0, 80), "right": (0, 80)},

    },
    "finger": {
        "mcp_flexion": {"left": (0, 90), "right": (0, 90)},
        "pip_flexion": {"left": (0, 100), "right": (0, 100)},
        "dip_flexion": {"left": (0, 90), "right": (0, 90)},
    },
}
