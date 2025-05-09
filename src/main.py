import threading
import os

from .utilities import *
from dotenv import load_dotenv
from .AutoSUAPS import AutoSUAPS
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field

# === ENV SETUP ===
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '../config/.env'), override=True)
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TOKEN = os.getenv("TOKEN")

# === API SETUP ===
app = FastAPI()
auto = AutoSUAPS(USERNAME, PASSWORD)    


def verify_token(token: str = Header(..., description="Token requis dans les headers")):
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")
    
    if token != TOKEN :
        raise HTTPException(status_code=403, detail="Token invalide")
    
    return token

@app.get('/api/activities')
def home(token = Depends(verify_token)):
    """ 
    Donne des informations utiles sur tous les créneaux à venir, les créneaux réservés, et ceux de la config
    """
    
    auto.login()
    activities_dict = auto.get_info_activites().to_dict(orient='records')
    auto.logout()
    
    config_file = read_config()
    sports = sorted(list({activity['activity_name'] for activity in activities_dict}))
    
    return {'activity_dict' : activities_dict, 
            'config' : config_file,
            'sports' : sports}


class CreneauResa(BaseModel):
    id_creneau_a_resa : str = Field(..., description='ID du créneau à réserver instantanément (attention ID de créneau != ID d\'activité)', example='a67dzs4zdz5')

@app.post('/api/reserver')
def reserver(request : CreneauResa, token = Depends(verify_token)) :
    """ 
    Réserve instantanément une activité précise
    """
    activity_id = request.id_creneau_a_resa
    
    auto.login()
    auto.set_periode(False)
    success = auto.reserver_creneau(activity_id)
    auto.logout()
    
    if not success :
        raise HTTPException(400, 'Erreur inconnue')
    
    return {'message' : f"Réservation effectuée pour l'activité ID : {activity_id}"}

class UpdateResa(BaseModel) :
    action: str = Field(..., description="Action à effectuer : 'sauvegarder' ou 'default'", example='sauvegarder')
    ids : list = Field(..., description='Liste des IDs des créneaux à réserver (pour la semaine à venir)', example=['a67dzs4zdz5', 'bd7d5d454e5'])

@app.post('/api/update')
def update(request : UpdateResa, token = Depends(verify_token)):
    """ 
    Met a jour le scheduler avec les nouveaux créneaux à réserver de manière récurrente
    """
    
    auto.login()
    
    if request.action == 'sauvegarder' :
        selected_ids : list = request.ids
        save_config({"ids_resa": selected_ids})
        setAllSchedules(auto)
        
    else :
        setDefaultSchedules(auto)

    auto.logout()
    return {'message' : 'Config ok !'}

# === MAIN ENTRY ===
def main():
    setAllSchedules(auto)

    threading.Thread(target=scheduler_loop, daemon=True).start()

if __name__ == '__main__':    
    main()
