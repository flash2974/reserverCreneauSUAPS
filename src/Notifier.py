import logging

import requests


class Notifier:
    def __init__(self, webhook_url: str = None, discord_id: str = None, gotify_url: str = None, gotify_token: str = None):
        """Gestionnaire de notifications

        Args:
            webhook_url (str): URL du WebHook Discord.
            discord_id (str): Identifiant Discord de la personne à ping.
            gotify_url (str): URL du serveur Gotify.
            gotify_token (str): Token d'authentification pour Gotify.
        """
        self.webhook_url = webhook_url
        self.discord_id = discord_id
        self.gotify_url = gotify_url
        self.gotify_token = gotify_token
        
    def notify(self, message: str) -> None:
        """Notifie l'utilisateur du succès ou de l'échec de la réservation via WebHook Discord.
        Si WEBHOOK_URL est None, print juste le message
        Si l'URL Gotify est précisée, envoie le message à Gotify.
        Si l'ID Discord de l'utilisateur est précisé, ping cet utilisateur.

        Args:
            message (str): Message à envoyer.
        """
        if self.webhook_url:
            data = {
                "content": f"{message}\n||<@{self.discord_id}>||"
                if self.discord_id
                else message,
                "username": "SUAPS - Daemon",
                "avatar_url": "https://fantasytopics.com/wp-content/uploads/2022/07/james-bousema-balrog-final.jpg.webp",
            }
            requests.post(self.webhook_url, data)
        
        if self.gotify_url and self.gotify_token:
            response = requests.post(
                self.gotify_url,
                headers = {
                    "X-Gotify-Key": f"{self.gotify_token}"
                },
                data = {
                    "title": "",
                    "message": f"{message}",
                    "priority": 5
                },
                timeout = 15
            )

        logging.info(message)
