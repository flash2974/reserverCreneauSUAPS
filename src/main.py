import time
import threading
import schedule
import datetime
import pytz
import json
import os
import logging

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from functools import wraps
from AutoSUAPS import AutoSUAPS
from utilities import setAllSchedules, setDefaultSchedules, get_paris_datetime

# === ENV SETUP ===
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '../config/.env'), override=True)
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TOKEN = os.getenv("TOKEN")

# === FLASK APP SETUP ===
app = Flask(__name__)
auto = AutoSUAPS(USERNAME, PASSWORD)    


def token_required(func):
    @wraps(func)  # Préserve le nom et les métadonnées de la fonction décorée
    def wrapper_func(*args, **kwargs):
        token = request.headers.get('Token') 
        if not token or token != TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper_func

@app.route('/api/activities')
@token_required
def home():
    activities_dict = get_activities()
    config_file = read_config()
    sports = sorted(list({activity['activity_name'] for activity in activities_dict}))
    
    json_to_return = {'activity_dict' : activities_dict, 
                      'config' : config_file,
                      'sports' : sports}
    
    return jsonify(json_to_return), 200



@app.route('/api/reserver', methods=['POST'])
@token_required
def reserver():
    data : dict = request.get_json()
    if not (activity_id := data.get('id_creneau_a_resa')):
        return jsonify({"error": "Pas de data"}), 400
    
    auto.login()
    auto.set_periode(False)
    success = auto.reserver_creneau(activity_id)
    auto.logout()
    
    return (jsonify({'message' : f"Réservation effectuée pour l'activité ID : {activity_id}"}), 201) if success else (jsonify({"error": "Erreur inconnue !"}), 400)

@app.route('/api/update', methods=['POST'])
@token_required
def update():
    data : dict = request.get_json()
    auto.login()
    action = data.get('action')
    
    if action == 'sauvegarder':
        selected_ids : list = data.get('ids')
        save_config({"ids_resa": selected_ids})
        setAllSchedules(auto)
        
    elif action == 'default':
        setDefaultSchedules(auto)

    auto.logout()
    return jsonify({'message' : 'Config ok !'}), 200

# === UTILS ===
def read_config():
    with open(os.path.join(BASE_DIR, '../config/config.json'), 'r') as f:
        return json.load(f)

def save_config(config):
    with open(os.path.join(BASE_DIR, '../config/config.json'), 'w') as f:
        json.dump(config, f, indent=4)

def get_activities():
    return auto.get_info_activites().to_dict(orient='records')



# === SCHEDULER ===
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

# === MAIN ENTRY ===
def main(DEBUG):
    auto.login()
    auto.print_ids()
    auto.logout()
    setAllSchedules(auto)

    threading.Thread(target=scheduler_loop, daemon=True).start()

    print("[INFO] Flask UI active sur http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)

if __name__ == '__main__':
    DEBUG = False
    if not DEBUG :
        logging.getLogger('werkzeug').setLevel(logging.CRITICAL) # pas de pollution (GET 304 machin)
        
    main(DEBUG)
