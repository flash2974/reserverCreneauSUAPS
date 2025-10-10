import os
import pytz
import json
import datetime

JSON_FILE = os.path.join(os.path.dirname(__file__), "../config/config.json")


def read_config():
    with open(JSON_FILE, "r") as f:
        return json.load(f)


def save_config(config):
    with open(JSON_FILE, "w") as f:
        json.dump(config, f, indent=4)


def read_id_list():
    return list(read_config()["ids_resa"])


def get_paris_datetime():
    return datetime.datetime.now(pytz.timezone("Europe/Paris"))
