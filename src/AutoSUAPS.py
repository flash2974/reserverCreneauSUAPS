from utilities import *
from datetime import datetime, timedelta
# import datetime
import requests
import json
from bs4 import BeautifulSoup
import pandas as pd

class AutoSUAPS :
    def __init__(self, username : str, password : str) -> None :
        '''
        Permet de gérer les réservations de créneaux pour le SUAPS<br>
        Paramètres :
        - `username` : identifiant de l'université
        - `password` : mot de passe
        '''
        self.username = username
        self.password = password

    def login(self) -> None :
        '''
        Permet de se connecter à son compte de l'université avec son username et password.
        '''
        self.session = requests.Session()
        r = self.session.get('https://cas6n.univ-nantes.fr/esup-cas-server/login?service=https%3A%2F%2Fu-sport.univ-nantes.fr%2Fcas%2F')

        page_login = BeautifulSoup(r.text, 'html.parser')
        inputs : list = page_login.find(id='fm1').find_all('input')

        login_data = {}
        for dico_input in inputs :
            if dico_input.attrs.get('value') is not None :
                login_data[dico_input['name']] = dico_input['value']
        login_data["username"] = self.username
        login_data["password"] = self.password

        self.session.post(r.url, login_data)
        
        self.setIDPeriode() 

    def getEtudiant(self) -> str :
        '''
        Retourne la data JSON de l'étudiant en question (de toi qui lis ce code)
        '''
        return self.session.get('https://u-sport.univ-nantes.fr/api/individus/me').json()
        
    
    def getCreneau(self, id_creneau : str, id_activite : str) -> str | None:
        '''
        Retourne les data JSON d'un créneau à partir de son ID et de l'ID de l'activité
        '''
        URL = f'https://u-sport.univ-nantes.fr/api/extended/creneau-recurrents/semaine?idActivite={id_activite}&idPeriode={self.id_periode}&idIndividu={self.username}'
        rep = self.session.get(URL).json()
        
        for creneau in rep :
            if creneau['id'] == id_creneau :
                return creneau
        return None

    def setIDPeriode(self) -> str :
        '''
        Fait une requête pour savoir quel catalogue utiliser, selon la date actuelle. 
        Soit le catalogue régulier, soit les différents catalogues selon les dates de vacances.
        '''
        rep = self.session.get('https://u-sport.univ-nantes.fr/api/extended/periodes/catalogue?idCatalogue=')
        
        if not isinstance(rep.json(), list) :
            self.id_periode = rep.json()['id']

        else :
            todayDate = getParisDatetime()
            dates = {}
            for periode in rep.json() :
                id = periode['id']
                
                # On enlève 1 semaine car on fait la réservation 1 semaine en avance
                startDate = datetime.strptime(periode['dateDebutActivites'], '%Y-%m-%d') - timedelta(days=7)
                endDate = datetime.strptime(periode['dateFinActivites'], '%Y-%m-%d') - timedelta(days=7)
                
                startDate = startDate.replace(tzinfo=todayDate.tzinfo)
                endDate = endDate.replace(tzinfo=todayDate.tzinfo)
                dates[id] = [startDate, endDate]
            
            closest_key = list(dates.keys())[0]
            
            # Pour savoir la tranche de dates la plus rapprochée de la date actuelle
            for key, slice_date in dates.items() :
                if (slice_date[0] <= todayDate <= slice_date[1] and
                dates[closest_key][0] < slice_date[0] and
                dates[closest_key][1] > slice_date[1]) :
                    closest_key = key
            
            self.id_periode = closest_key
        
                    
    def getActivities(self) -> list[str] :
        '''
        Renvoie une liste contenant les IDs des activités de l'user (3 max)
        '''
        url_3sports = f'https://u-sport.univ-nantes.fr/api/extended/activites/individu/paiement?idIndividu={self.username}&typeIndividu={self.getEtudiant()["type"]}&idPeriode={self.id_periode}'
        rep = self.session.get(url_3sports).json()
        
        activities = []
        for activity in rep['activites'] :
            activities.append(activity['id'])
            
        return activities
    
    def getActivitiesInfo(self) -> pd.DataFrame :
        '''
        Renvoie un dataframe avec toutes les infos sur les créneaux disponibles
        '''
        activities_list = []
        ordered_days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        for activity_id in self.getActivities():
            URL = f'https://u-sport.univ-nantes.fr/api/extended/creneau-recurrents/semaine?idActivite={activity_id}&idPeriode={self.id_periode}&idIndividu={self.username}'
            rep = self.session.get(URL).json()

            if len(rep) > 0 : 
                activity_name = rep[0]["activite"]['nom']
                for activity in rep:
                    jour = activity['jour'].capitalize()
                    creneau_horaire = activity['horaireDebut'] + ' - ' + activity['horaireFin']
                    lieu = activity['localisation']['nom']
                    
                    activities_list.append({
                        'activity_name': activity_name,
                        'activity_id': activity_id,
                        'jour': jour,
                        'creneau_horaire': creneau_horaire,
                        'lieu' : lieu,
                        'places_restantes' : activity['quota'] - activity['nbInscrits'],
                        'id': activity['id']
                    })
            
        df = pd.DataFrame(activities_list)
        if not df.empty:
            df['jour'] = pd.Categorical(df['jour'], categories=ordered_days, ordered=True)
            df = df.sort_values(['jour', 'creneau_horaire'])
            df.reset_index(inplace=True, drop=True)
            
        return df
        
    
    def getSchedules(self, delta : int = 2, liste_input: list[str] = readJSON()) -> list[dict]:
        '''
        Pour chaque activité de liste_input, récupère l'heure de fin du créneau et ajoute 2 minutes (delta) pour savoir à quelles heures set les schedules
        '''
        if (df := self.getActivitiesInfo()).empty :
            return None
        
        filtered_rows = df[df['id'].isin(liste_input)]

        res = []
        for _, row in filtered_rows.iterrows():
            id = row['id']
            day = row['jour'].lower()
            
            end_time = datetime.strptime(row['creneau_horaire'].split(' - ')[1], "%H:%M")

            end_time_plus_delta = end_time + timedelta(minutes=delta)
            hour = end_time_plus_delta.strftime("%H:%M")
            
            res.append({'id': id, "day" : day, "hour" : hour})
        
        return res
        
    def printIDs(self) -> None :
        '''
        Affiche le tableaux des activités disponibles, avec quelques informations
        '''
        if(df := self.getActivitiesInfo()).empty :
            print("Aucune activité disponible.")
        else :
            df = df.drop(["activity_id"], axis=1)
            print(df.to_string(index=False))
        
    
    def reserverCreneau(self, id_creneau: str) -> None:
        '''
        Réserve le créneau spécifié par son id
        '''
        df = self.getActivitiesInfo()

        print(getParisDatetime().strftime("%d-%m-%Y %H:%M:%S"), end=' --> ')

        try:
            row = df.loc[df['id'] == id_creneau].iloc[0]
            activity_id = row['activity_id']
            creneau_id = row['id']
            places_restantes = row['places_restantes']
            
        except IndexError:
            print("Aucun créneau trouvé avec cet id")
            
        except Exception as e:
            print(f"Erreur d'accès: {e}")

        else :
            if places_restantes > 0:
                res = self.poster_requete(creneau_id, activity_id)
                if res == 201:
                    print(f"Inscription effectuée en {row['activity_name']}, le {row['jour']} pour le créneau de {row['creneau_horaire']}")
                else:
                    print(f"Erreur {res} d'inscription en {row['activity_name']}, le {row['jour']} pour le créneau de {row['creneau_horaire']}")
            else:
                print(f"Pas de place en {row['activity_name']}, le {row['jour']} pour le créneau de {row['creneau_horaire']}")
            print()


    def poster_requete(self, id_creneau : str, id_activite : str) -> int :
        '''
        Envoie une requête POST pour réserver un créneau
        '''
        postURL = f'https://u-sport.univ-nantes.fr/api/extended/reservation-creneaux?idPeriode={self.id_periode}'

        post_data = {
            "utilisateur": {
                "login": self.username,
                "typeUtilisateur": self.getEtudiant()["type"]
            },
            'dateReservation': datetime.now().isoformat(timespec='milliseconds') + 'Z',
            'actif': False,
            'forcage': False,
            'creneau': self.getCreneau(id_creneau,id_activite),
            "individuDTO": self.getEtudiant()
        }
        
        post_data["creneau"]["fileAttente"] = True
        post_data["creneau"]["actif"] = True
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Convertir les données en JSON
        post_data_json = json.dumps(post_data)

        rep = self.session.post(postURL, 
                                data = post_data_json, 
                                headers = headers)

        return rep.status_code
    
    def logout(self) -> None : 
        '''
        Ferme la session HTTP et donc déconnecte l'utilisateur
        '''
        self.session.close()