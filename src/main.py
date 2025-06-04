import os
import pytz
import time
import logging
import schedule
import datetime
import threading

from dotenv import load_dotenv
from AutoSUAPS import AutoSUAPS
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from utilities import set_all_schedules, set_default_schedules, get_paris_datetime, save_config, read_config

# === ENV SETUP ===
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '../config/.env'), override=True)
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TOKEN = os.getenv("TOKEN")

# === FLASK APP SETUP ===
app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

activities_cache = None
activities_cache_timestamp = 0
CACHE_EXPIRATION_TIME = 600  # seconds

auto = AutoSUAPS(USERNAME, PASSWORD)    

# === FLASK AUTH ===
class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and request.args.get('token') == TOKEN:
        user = User("admin")
        login_user(user, remember=True)
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        password = request.form['password']
        want_remember = 'remember' in request.form
        
        if password == PASSWORD:
            user = User("admin")
            login_user(user, remember=want_remember)
            return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    activities_dict = get_activities()
    config_file = read_config()
    
    sports = sorted(list({activity['activity_name'] for activity in activities_dict}))

    return render_template('index.html', activities_dict=activities_dict, config_file=config_file, sports=sports)



@app.route('/reserver', methods=['POST'])
@login_required
def reserver():
    activity_id = request.form.get('id_resa')  # Récupère l'ID de l'activité sélectionnée
    if not activity_id:
        flash("Aucune activité sélectionnée pour la réservation.", "error")
        return redirect('/')
    
    with auto :
        auto.set_periode(False)
        auto.reserver_creneau(activity_id)
    
    print(f"Réservation effectuée pour l'activité ID : {activity_id}")
    flash(f"Réservation effectuée !", "success")
    return redirect('/')

@app.route('/update', methods=['POST'])
@login_required
def update():
    action = request.form.get('action')
    
    with auto :

        if action == 'sauvegarder':
            selected_ids = request.form.getlist('id_resa')
            save_config({"ids_resa": selected_ids})
            set_all_schedules(auto)
            flash('Sauvegardé !')

        elif action == 'default':
            set_default_schedules(auto)
            flash('Réservations par défaut ok !')
            
        elif action.startswith("reserver_"):
            activity_id = action.split("_")[1]
            auto.set_periode(False)
            auto.reserver_creneau(activity_id)
            flash(f"Réservation effectuée !", "success")

    return redirect(url_for('home'))

# === UTILS ===
def get_activities():
    global activities_cache, activities_cache_timestamp
    current_time = time.time()
    if activities_cache is None or (current_time - activities_cache_timestamp) > CACHE_EXPIRATION_TIME:
        with auto :
            df = auto.get_info_activites()
            activities_cache = df.to_dict(orient='records')
            activities_cache_timestamp = current_time
    return activities_cache

# === SCHEDULER ===
def scheduler_loop():
    counter = 0
    old_run = datetime.datetime(1970, 1, 1)
    
    while get_paris_datetime().second != 0 :
        time.sleep(1)
            
    while True:
        schedule.run_pending()
        
        if counter % 10 == 0:
            next_job = min(schedule.jobs, key=lambda job: job.next_run)
            next_run = next_job.next_run
            
            if next_run and next_run != old_run:
                note = getattr(next_job, 'note', '???')
                print(f"Prochaine exécution : {next_run.astimezone(pytz.timezone('Europe/Paris')).strftime('%d-%m-%Y %H:%M:%S')} ({note})")
                old_run = next_run
                
        time.sleep(60)
        counter += 1

# === MAIN ENTRY ===
def main(DEBUG):
    with auto :
        set_all_schedules(auto)

    threading.Thread(target=scheduler_loop, daemon=True).start()

    app.run(host="0.0.0.0", port=5000, debug=DEBUG)

if __name__ == '__main__':
    DEBUG = False
    if not DEBUG :
        logging.getLogger('werkzeug').setLevel(logging.CRITICAL) # pas de pollution (GET 304 machin)
        
    main(DEBUG)