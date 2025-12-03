import json
from datetime import datetime, timedelta
from random import randint

import pandas as pd
import requests
import schedule
from bs4 import BeautifulSoup

from src.Notifier import Notifier
from src.utilities import get_paris_datetime, read_id_list


class AutoSUAPS:
    def __init__(self, username: str, password: str, notifier: Notifier = None) -> None:
        """
        Permet de gérer les réservations de créneaux pour le SUAPS

        Args:
            username (str): Identifiant de l'université
            password (str): Mot de passe
        """
        self.username = username
        self.password = password
        self.notifier = notifier

    def login(self) -> None:
        """
        Établit une session authentifiée avec le système CAS de l'université.

        Raises:
            Exception: Si les identifiants sont incorrects (code 401)
            Exception: Pour toute autre erreur de connexion
        """
        self.session = requests.Session()
        r = self.session.get(
            "https://cas6n.univ-nantes.fr/esup-cas-server/login?service=https%3A%2F%2Fu-sport.univ-nantes.fr%2Fcas%2F"
        )

        page_login = BeautifulSoup(r.text, "html.parser")
        inputs: list = page_login.find(id="fm1").find_all("input")

        login_data = {}
        for dico_input in inputs:
            if dico_input.attrs.get("value") is not None:
                login_data[dico_input["name"]] = dico_input["value"]
        login_data["username"] = self.username
        login_data["password"] = self.password

        res_code = self.session.post(r.url, login_data).status_code

        if res_code in (201, 200):
            self.set_periode()
        elif res_code == 401:
            raise Exception("Incorrect password")
        else:
            raise Exception(f"Error ! code {res_code}")

    def get_etudiant(self) -> dict:
        """
        Récupère les infos de l'étudiant (JSON renvoyé par l'API du SUAPS)

        Returns:
            dict: Data de l'étudiant
        """
        return self.session.get(
            "https://u-sport.univ-nantes.fr/api/individus/me"
        ).json()

    def get_creneau_info(self, id_creneau: str, id_activite: str) -> dict | None:
        """
        Récupère les données JSON d'un créneau

        Args:
            id_creneau (str): ID du créneau dont on souhaite avoir les détails
            id_activite (str): ID de l'activité dudit créneau

        Returns:
            dict: Data JSON du créneau en question
        """
        URL = f"https://u-sport.univ-nantes.fr/api/extended/creneau-recurrents/semaine?idActivite={id_activite}&idPeriode={self.id_periode}&idIndividu={self.username}"
        rep = self.session.get(URL).json()

        for creneau in rep:
            if creneau["id"] == id_creneau:
                return creneau
        return None

    def set_periode(self) -> str:
        """
        Fait une requête pour savoir quel catalogue utiliser, selon la date actuelle.
        Soit le catalogue régulier, soit les différents catalogues selon les dates de vacances.

        Returns:
            str: ID du catalogue
        """
        rep = self.session.get(
            "https://u-sport.univ-nantes.fr/api/extended/periodes/catalogue?idCatalogue="
        )
        data = rep.json()

        if not isinstance(data, list):
            self.id_periode = data["id"]
        else:
            todayDate = get_paris_datetime()
            for periode in data:
                startDate = datetime.strptime(
                    periode["dateDebutInscriptions"], "%Y-%m-%d"
                ).replace(tzinfo=todayDate.tzinfo)
                endDate = datetime.strptime(
                    periode["dateFinInscriptions"], "%Y-%m-%d"
                ).replace(tzinfo=todayDate.tzinfo)
                if startDate <= todayDate <= endDate:
                    self.id_periode = periode["id"]
                    break
            else:
                self.id_periode = data[0]["id"]

    def get_activites(self) -> list[str]:
        """
        Récupère les activités auxquelles est inscrit l'utilisateur connecté (3 max)

        Returns:
            list[str] : liste contenant les IDs des activités de l'user
        """
        url_3sports = f"https://u-sport.univ-nantes.fr/api/extended/activites/individu/paiement?idIndividu={self.username}&typeIndividu={self.get_etudiant()['type']}&idPeriode={self.id_periode}"
        rep = self.session.get(url_3sports).json()

        activities = []
        for activity in rep["activites"]:
            activities.append(activity["id"])

        return activities

    def get_all_creneaux(self) -> pd.DataFrame:
        """
        Récupère toutes les informations des créneaux (horaires, type de sport, localisation, etc)

        Returns:
            pd.DataFrame: Dataframe avec toutes les infos sur les créneaux disponibles
        """
        activities_list = []
        ordered_days = [
            "Lundi",
            "Mardi",
            "Mercredi",
            "Jeudi",
            "Vendredi",
            "Samedi",
            "Dimanche",
        ]
        liste_resa = self.get_creneaux_inscrit()
        for activity_id in self.get_activites():
            URL = f"https://u-sport.univ-nantes.fr/api/extended/creneau-recurrents/semaine?idActivite={activity_id}&idPeriode={self.id_periode}&idIndividu={self.username}"
            rep = self.session.get(URL).json()

            if len(rep) > 0:
                activity_name = rep[0]["activite"]["nom"]
                for activity in rep:
                    jour = activity["jour"].capitalize()
                    creneau_horaire = (
                        activity["horaireDebut"] + " - " + activity["horaireFin"]
                    )
                    lieu = activity["localisation"]["nom"]
                    id = activity["id"]

                    if len(activity_name) > 20:
                        activity_name = "".join(
                            [word[0] for word in activity_name.split("-")[1].split()]
                        )

                    activities_list.append(
                        {
                            "activity_name": activity_name,
                            "activity_id": activity_id,
                            "jour": jour,
                            "creneau_horaire": creneau_horaire,
                            "lieu": lieu,
                            "places_restantes": activity["quota"]
                            - activity["nbInscrits"],
                            "id": id,
                            "resa_a_venir": id in liste_resa,
                        }
                    )

        df = pd.DataFrame(activities_list)
        if not df.empty:
            df["jour"] = pd.Categorical(
                df["jour"], categories=ordered_days, ordered=True
            )
            df = df.sort_values(["jour", "creneau_horaire"])
            df.reset_index(inplace=True, drop=True)

        return df

    def get_schedules(self) -> list[dict]:
        """
        Pour chaque activité de liste_input, récupère l'heure de fin du créneau et ajoute un delta random pour savoir à quelles heures fixer les schedules.

        Returns:
            list[dict]: Chaque dictionnaire représente un créneau à fixer, avec son ID, jour, heure, et un nom.
        """
        liste_input = read_id_list()
        if (df := self.get_all_creneaux()).empty:
            return None

        filtered_rows = df[df["id"].isin(liste_input)]

        res = []
        for _, row in filtered_rows.iterrows():
            id = row["id"]
            day = row["jour"].lower()
            name = row["activity_name"]

            end_time = datetime.strptime(
                row["creneau_horaire"].split(" - ")[1], "%H:%M"
            )

            end_time_plus_delta = end_time + timedelta(seconds=randint(60, 180))
            hour = end_time_plus_delta.strftime("%H:%M:%S")

            res.append({"id": id, "day": day, "hour": hour, "name": name})

        return res

    def get_creneaux_inscrit(self) -> list[str]:
        """
        Récupère les créneaux auxquels est inscrit l'utilisateur.

        Returns:
            list[str]: Liste des IDS desdits créneaux.
        """
        rep = self.session.get(
            f"https://u-sport.univ-nantes.fr/api/extended/reservation-creneaux?idIndividu={self.username}"
        ).json()
        res = []
        dateAuj = get_paris_datetime()

        for creneau in rep:
            dateDebut = datetime.strptime(
                creneau["occurenceCreneauDTO"]["debut"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=dateAuj.tzinfo)
            if creneau["actif"] and dateAuj < dateDebut:
                res.append(creneau["creneau"]["id"])
        return res

    def __str__(self) -> None:
        """
        Affiche le tableaux des activités disponibles, avec quelques informations.
        """
        if (df := self.get_all_creneaux()).empty:
            return "Aucune activité disponible."
        else:
            df = df.drop(["activity_id"], axis=1)
            return df.to_string(index=False)

    def reserver_creneau(self, id_creneau: str) -> None:
        """
        Réserve le créneau spécifié par son id et notifie l'utilisateur (s'il le souhaite).

        Args:
            id_creneau (str): ID du créneau à réserver
        """
        df = self.get_all_creneaux()

        try:
            row = df.loc[df["id"] == id_creneau].iloc[0]
            activity_id = row["activity_id"]
            creneau_id = row["id"]
            places_restantes = row["places_restantes"]

        except Exception as e:
            message = f"Erreur inconnue : {e}"

        else:
            if places_restantes > 0:
                res = self.poster_requete(creneau_id, activity_id)
                if res == 201:
                    message = f"Inscription effectuée en {row['activity_name']}, le {row['jour']} pour le créneau de {row['creneau_horaire']}"
                else:
                    message = f"Erreur {res} d'inscription en {row['activity_name']}, le {row['jour']} pour le créneau de {row['creneau_horaire']}"
            else:
                message = f"Pas de place en {row['activity_name']}, le {row['jour']} pour le créneau de {row['creneau_horaire']}"

            self.notifier.notify(message)

    def poster_requete(self, id_creneau: str, id_activite: str) -> int:
        """
        Envoie une requête POST pour réserver un créneau.

        Args:
            id_creneau (str): ID du créneau à réserver.
            id_activite (str): ID de l'activité associée au créneau.

        Returns:
            int: Code de retour de la requête POST. Succès si 201.
        """
        postURL = f"https://u-sport.univ-nantes.fr/api/extended/reservation-creneaux?idPeriode={self.id_periode}"

        post_data = {
            "utilisateur": {
                "login": self.username,
                "typeUtilisateur": self.get_etudiant()["type"],
            },
            "dateReservation": datetime.now().isoformat(timespec="milliseconds") + "Z",
            "actif": False,
            "forcage": False,
            "creneau": self.get_creneau_info(id_creneau, id_activite),
            "individuDTO": self.get_etudiant(),
        }

        post_data["creneau"]["fileAttente"] = True
        post_data["creneau"]["actif"] = True

        headers = {"Content-Type": "application/json"}

        # Convertir les données en JSON
        post_data_json = json.dumps(post_data)

        rep = self.session.post(url=postURL, data=post_data_json, headers=headers)

        return rep.status_code

    def logout(self) -> None:
        """
        Ferme la session HTTP et donc déconnecte l'utilisateur.
        """
        self.session.close()

    def __enter__(self):
        """
        Méthode d'entrée (quand on fait with AutoSUAPS ...).
        """
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Méthode de sortie (à la fin du bloc with AutoSUAPS ...).
        """
        self.logout()
        return False

    def actions(self, id: str):
        """
        Se log au CAS et réserve un créneau.

        Args:
            id (str): ID du créneau à réserver.
        """
        with self:
            self.reserver_creneau(id)

    def set_schedule(self, id: str, day: str, hour: str, name: str):
        """
        Rajoute une tâche récurrence avec Schedule (pour réserver un créneau)

        Args:
            id (str): ID du créneau à réserver.
            day (str): Jour : "lundi", "mardi", etc.
            hour (str): Heure : "12:05:00" par ex.
            name (str): Nom de l'activité : "Escalade", etc.
        """
        match day:
            case "lundi":
                job = (
                    schedule.every()
                    .monday.at(hour, "Europe/Paris")
                    .do(self.actions, id)
                )
            case "mardi":
                job = (
                    schedule.every()
                    .tuesday.at(hour, "Europe/Paris")
                    .do(self.actions, id)
                )
            case "mercredi":
                job = (
                    schedule.every()
                    .wednesday.at(hour, "Europe/Paris")
                    .do(self.actions, id)
                )
            case "jeudi":
                job = (
                    schedule.every()
                    .thursday.at(hour, "Europe/Paris")
                    .do(self.actions, id)
                )
            case "vendredi":
                job = (
                    schedule.every()
                    .friday.at(hour, "Europe/Paris")
                    .do(self.actions, id)
                )
            case "samedi":
                job = (
                    schedule.every()
                    .saturday.at(hour, "Europe/Paris")
                    .do(self.actions, id)
                )
            case "dimanche":
                job = (
                    schedule.every()
                    .sunday.at(hour, "Europe/Paris")
                    .do(self.actions, id)
                )

        job.note = name

    def set_all_schedules(self):
        """Fixe toutes les schedules en fonction de la config (les créneaux qu'on veut réserver de manière récurrente)."""
        schedule.clear()

        allSchedules = self.get_schedules()

        if allSchedules is None:
            return

        for creneau in allSchedules:
            self.set_schedule(
                id=creneau["id"],
                day=creneau["day"],
                hour=creneau["hour"],
                name=creneau["name"],
            )
