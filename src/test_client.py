import requests
import os
from dotenv import load_dotenv

# === ENV SETUP ===
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '../config/.env'), override=True)

TOKEN = os.getenv("TOKEN")

def try_get_activities() :
    rep = requests.get('http://localhost:5000/api/activities', headers={'token':TOKEN})
    
    print(rep.status_code)
    print(rep.content.decode('utf-8'))
    
    
def try_post() :
    rep = requests.post('http://localhost:5000/api/reserver', headers={'token':TOKEN}, json={"id_creneau_a_resa": "eba1eb76-55b8-4ae4-a067-6182f3e6707b"})
    
    print(rep.status_code)
    print(rep.content.decode('utf-8'))
    
try_get_activities()
# try_post()
