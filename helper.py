import os
import json

STATS_FILE = "performance.json"


def save_performance(perf_dict):
    with open(STATS_FILE, "w") as f:
        json.dump(perf_dict, f)


def load_performance():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {}
