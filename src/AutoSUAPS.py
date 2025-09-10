import json
import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from src.utilities import get_paris_datetime, read_id_list


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
        
        self.set_periode() 

    def get_etudiant(self) -> str :
        '''
        Retourne la data JSON de l'étudiant en question (de toi qui lis ce code)
        '''
        return self.session.get('https://u-sport.univ-nantes.fr/api/individus/me').json()
        
    
    def get_creneau(self, id_creneau : str, id_activite : str) -> str | None:
        '''
        Retourne les data JSON d'un créneau à partir de son ID et de l'ID de l'activité
        '''
        URL = f'https://u-sport.univ-nantes.fr/api/extended/creneau-recurrents/semaine?idActivite={id_activite}&idPeriode={self.id_periode}&idIndividu={self.username}'
        rep = self.session.get(URL).json()
        
        for creneau in rep :
            if creneau['id'] == id_creneau :
                return creneau
        return None

    def set_periode(self) -> str:
        '''
        Fait une requête pour savoir quel catalogue utiliser, selon la date actuelle.
        Soit le catalogue régulier, soit les différents catalogues selon les dates de vacances.
        '''
        rep = self.session.get('https://u-sport.univ-nantes.fr/api/extended/periodes/catalogue?idCatalogue=')
        data = rep.json()
    
        if not isinstance(data, list):
            self.id_periode = data['id']
        else:
            todayDate = get_paris_datetime()
            for periode in data:
                startDate = datetime.strptime(periode['dateDebutInscriptions'], '%Y-%m-%d').replace(tzinfo=todayDate.tzinfo)
                endDate = datetime.strptime(periode['dateFinInscriptions'], '%Y-%m-%d').replace(tzinfo=todayDate.tzinfo)
                if startDate <= todayDate <= endDate:
                    self.id_periode = periode['id']
                    break
            else:
                self.id_periode = data[0]['id']
                    
    def get_activites(self) -> list[str] :
        '''
        Renvoie une liste contenant les IDs des activités de l'user (3 max)
        '''
        url_3sports = f'https://u-sport.univ-nantes.fr/api/extended/activites/individu/paiement?idIndividu={self.username}&typeIndividu={self.get_etudiant()["type"]}&idPeriode={self.id_periode}'
        rep = self.session.get(url_3sports).json()
        
        activities = []
        for activity in rep['activites'] :
            activities.append(activity['id'])
            
        return activities
    
    def get_info_activites(self) -> pd.DataFrame :
        '''
        Renvoie un dataframe avec toutes les infos sur les créneaux disponibles
        '''
        activities_list = []
        ordered_days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        liste_resa = self.get_creneaux_inscrit()
        for activity_id in self.get_activites():
            URL = f'https://u-sport.univ-nantes.fr/api/extended/creneau-recurrents/semaine?idActivite={activity_id}&idPeriode={self.id_periode}&idIndividu={self.username}'
            rep = self.session.get(URL).json()

            if len(rep) > 0 : 
                activity_name = rep[0]["activite"]['nom']
                for activity in rep:
                    jour = activity['jour'].capitalize()
                    creneau_horaire = activity['horaireDebut'] + ' - ' + activity['horaireFin']
                    lieu = activity['localisation']['nom']
                    id = activity['id']
                    
                    activities_list.append({
                        'activity_name': activity_name,
                        'activity_id': activity_id,
                        'jour': jour,
                        'creneau_horaire': creneau_horaire,
                        'lieu' : lieu,
                        'places_restantes' : activity['quota'] - activity['nbInscrits'],
                        'id': id,
                        'resa_a_venir' : id in liste_resa
                    })
            
        df = pd.DataFrame(activities_list)
        if not df.empty:
            df['jour'] = pd.Categorical(df['jour'], categories=ordered_days, ordered=True)
            df = df.sort_values(['jour', 'creneau_horaire'])
            df.reset_index(inplace=True, drop=True)
            
        return df
        
    
    def get_schedules(self, delta : int = 2, liste_input: list[str] = read_id_list()) -> list[dict]:
        '''
        Pour chaque activité de liste_input, récupère l'heure de fin du créneau et ajoute 2 minutes (delta) pour savoir à quelles heures set les schedules
        '''
        if (df := self.get_info_activites()).empty :
            return None
        
        filtered_rows = df[df['id'].isin(liste_input)]

        res = []
        for _, row in filtered_rows.iterrows():
            id = row['id']
            day = row['jour'].lower()
            name = row['activity_name']
            
            end_time = datetime.strptime(row['creneau_horaire'].split(' - ')[1], "%H:%M")

            end_time_plus_delta = end_time + timedelta(minutes=delta)
            hour = end_time_plus_delta.strftime("%H:%M")
            
            res.append({"id": id, "day" : day, "hour" : hour, "name" : name})
        
        return res
    
    def get_creneaux_inscrit(self) -> list[str] :
        '''
        Renvoie les créneaux pour lesquels on est inscrit (créneaux à venir)
        '''
        rep = self.session.get('https://u-sport.univ-nantes.fr/api/extended/reservation-creneaux?idIndividu=E24A014X').json()
        res = []
        dateAuj = get_paris_datetime()
        
        for creneau in rep :
            
            dateDebut = datetime.strptime(creneau['occurenceCreneauDTO']['debut'], '%Y-%m-%dT%H:%M:%SZ')
            dateDebut = dateDebut.replace(tzinfo=dateAuj.tzinfo)
            
            if creneau['actif'] and dateAuj < dateDebut :
                res.append(creneau['creneau']['id'])
                
        return res
        
    def __str__(self) -> None :
        '''
        Affiche le tableaux des activités disponibles, avec quelques informations
        '''
        if(df := self.get_info_activites()).empty :
            return "Aucune activité disponible."
        else :
            df = df.drop(["activity_id"], axis=1)
            return df.to_string(index=False)
        
    
    def reserver_creneau(self, id_creneau: str) -> None:
        '''
        Réserve le créneau spécifié par son id
        '''
        df = self.get_info_activites()

        print(get_paris_datetime().strftime("%d-%m-%Y %H:%M:%S"), end=' --> ')

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
                "typeUtilisateur": self.get_etudiant()["type"]
            },
            'dateReservation': datetime.now().isoformat(timespec='milliseconds') + 'Z',
            'actif': False,
            'forcage': False,
            'creneau': self.get_creneau(id_creneau,id_activite),
            "individuDTO": self.get_etudiant()
        }
        
        post_data["creneau"]["fileAttente"] = True
        post_data["creneau"]["actif"] = True
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Convertir les données en JSON
        post_data_json = json.dumps(post_data)

        rep = self.session.post(url = postURL, 
                                data = post_data_json, 
                                headers = headers)

        return rep.status_code
    
    def logout(self) -> None : 
        '''
        Ferme la session HTTP et donc déconnecte l'utilisateur
        '''
        self.session.close()
        
        
    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()
        return False