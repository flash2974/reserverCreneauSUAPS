import json
from flask import Flask, render_template, request, redirect, url_for, flash

from AutoSUAPS import *
from dotenv import load_dotenv
from os import getenv
import time
import schedule
import os

BASE_DIR = os.path.dirname(__file__)

load_dotenv(dotenv_path=os.path.join(BASE_DIR, '../config/.env'), override=True)
USERNAME = getenv("USERNAME")
PASSWORD = getenv("PASSWORD")

app = Flask(__name__)
app.secret_key = os.urandom(24)

activities_cache = None
activities_cache_timestamp = 0
CACHE_EXPIRATION_TIME = 600 # Time in seconds

def read_config():
    with open(os.path.join(BASE_DIR, '../config/config.json'), 'r') as config_file:
        return json.load(config_file)

def save_config(config):
    with open(os.path.join(BASE_DIR, '../config/config.json'), 'w') as config_file:
        json.dump(config, config_file, indent=4)

def get_activities():
    global activities_cache, activities_cache_timestamp
    current_time = time.time()

    if activities_cache is None or (current_time - activities_cache_timestamp) > CACHE_EXPIRATION_TIME:
        auto = AutoSUAPS(USERNAME, PASSWORD)
        auto.login()
        df = auto.getActivitiesInfo()
        activities_cache = df.to_dict(orient='records')
        activities_cache_timestamp = current_time
        auto.logout()

    return activities_cache

@app.route('/')
def home():
    activities_dict = get_activities()

    return render_template('index.html', activities_dict = activities_dict)

@app.route('/update', methods=['POST'])
def update():
    selected_ids = request.form.getlist('id_resa')

    if selected_ids:
        save_config({"ids_resa": list(selected_ids)})
    else:
        save_config({"ids_resa": []})
    
    flash('Modifications enregistrées !')
    

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
