import os
import pytz
import json
import schedule
import datetime

JSON_FILE = os.path.join(os.path.dirname(__file__), '../config/config.json')

def read_config():
    with open(JSON_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(JSON_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def read_id_list() :
    return list(read_config()["ids_resa"])

def get_paris_datetime() :
    return datetime.datetime.now(pytz.timezone('Europe/Paris'))


def actions(auto, id) :
    with auto :
        auto.reserver_creneau(id)
    

def set_schedule(id, day, hour, name, auto):
    match day:
        case "lundi":
            job = schedule.every().monday.at(hour, "Europe/Paris").do(actions, auto, id)
        case "mardi":
            job = schedule.every().tuesday.at(hour, "Europe/Paris").do(actions, auto, id)
        case "mercredi":
            job = schedule.every().wednesday.at(hour, "Europe/Paris").do(actions, auto, id)
        case "jeudi":
            job = schedule.every().thursday.at(hour, "Europe/Paris").do(actions, auto, id)
        case "vendredi":
            job = schedule.every().friday.at(hour, "Europe/Paris").do(actions, auto, id)
        case "samedi":
            job = schedule.every().saturday.at(hour, "Europe/Paris").do(actions, auto, id)
        case "dimanche":
            job = schedule.every().sunday.at(hour, "Europe/Paris").do(actions, auto, id)
    
    job.note = name


def set_all_schedules(auto):
    schedule.clear()
    
    if(allSchedules := auto.get_schedules()) is None :
        return
    for creneau in allSchedules :
        set_schedule(
            id = creneau['id'], 
            day = creneau['day'], 
            hour = creneau['hour'], 
            name = creneau['name'],
            auto = auto
        )


def set_default_schedules(auto) :
    data = {"ids_resa": ["a67c920a-fc66-452c-8d07-5d7206a44f5b", "c12b09b0-8660-4b3c-9711-983317af0441", "eba1eb76-55b8-4ae4-a067-6182f3e6707b"]}
    
    with open(JSON_FILE, 'w') as file :
        json.dump(data, file, indent=4)
        
    schedule.clear()
    
    schedule.every().wednesday.at("21:47", "Europe/Paris").do(actions, auto, data["ids_resa"][0])
    schedule.every().thursday.at("19:33", "Europe/Paris").do(actions, auto, data["ids_resa"][1])
    schedule.every().tuesday.at("20:03", "Europe/Paris").do(actions, auto, data["ids_resa"][2])