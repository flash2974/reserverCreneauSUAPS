# Pas d'import de AutoSUAPS pour éviter un import circulaire
import schedule
import datetime
import pytz
import json
import os
import time

BASE_DIR = os.path.dirname(__file__)

def readJSON() :
    with open(os.path.join(BASE_DIR, '../config/config.json'), 'r') as file :
        return list(json.load(file)["ids_resa"])

def get_paris_datetime() :
    return datetime.datetime.now(pytz.timezone('Europe/Paris'))


def actions(auto, id) :
    auto.login()
    auto.reserver_creneau(id)
    auto.logout()
    

def setSchedule(id, day, hour, name, auto):
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


def setAllSchedules(auto):
    schedule.clear()
    
    if(allSchedules := auto.get_schedules()) is None :
        return
    for creneau in allSchedules :
        setSchedule(
            id = creneau['id'], 
            day = creneau['day'], 
            hour = creneau['hour'], 
            name = creneau['name'],
            auto = auto
        )


def setDefaultSchedules(auto) :
    data = {"ids_resa": ["a67c920a-fc66-452c-8d07-5d7206a44f5b", "c12b09b0-8660-4b3c-9711-983317af0441", "eba1eb76-55b8-4ae4-a067-6182f3e6707b"]}
    
    with open(os.path.join(BASE_DIR, '../config/config.json'), 'w') as file :
        json.dump(data, file, indent=4)
        
    schedule.clear()
    
    schedule.every().wednesday.at("21:47", "Europe/Paris").do(actions, auto, data["ids_resa"][0])
    schedule.every().thursday.at("19:33", "Europe/Paris").do(actions, auto, data["ids_resa"][1])
    schedule.every().tuesday.at("20:03", "Europe/Paris").do(actions, auto, data["ids_resa"][2])
    

# === UTILS ===
def read_config():
    with open(os.path.join(BASE_DIR, '../config/config.json'), 'r') as f:
        return json.load(f)

def save_config(config):
    with open(os.path.join(BASE_DIR, '../config/config.json'), 'w') as f:
        json.dump(config, f, indent=4)


def scheduler_loop():
    counter = 0
    old_run = datetime.datetime(1970, 1, 1)
    
    while get_paris_datetime().second != 0 :
        time.sleep(1)
            
    while True:
        schedule.run_pending()
        
        if counter % 10 == 0:
            next_job = schedule.jobs[0]
            next_run = next_job.next_run
            
            if next_run and next_run != old_run:
                note = getattr(next_job, 'note', '???')
                print(f"Prochaine exécution : {next_run.astimezone(pytz.timezone('Europe/Paris')).strftime('%d-%m-%Y %H:%M:%S')} ({note})")
                old_run = next_run
                
        time.sleep(60)
        counter += 1