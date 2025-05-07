import requests
import os
from dotenv import load_dotenv

# === ENV SETUP ===
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '../config/.env'), override=True)

TOKEN = os.getenv("TOKEN")

def try_get_activities() :
    rep = requests.get('http://localhost:5000/api/activities', headers={'Token':TOKEN})
    
    print(rep.status_code)
    print(rep.content)
    
try_get_activities()
