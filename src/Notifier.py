import requests
import logging


class Notifier:
    def __init__(self, webhook_url: str = None, discord_id: str = None):
        """Gestionnaire de notifications

        Args:
            webhook_url (str): URL du WebHook Discord.
            discord_id (str): Identifiant Discord de la personne à ping.
        """
        self.webhook_url = webhook_url
        self.discord_id = discord_id

    def notify(self, message: str) -> None:
        """Notifie l'utilisateur du succès ou de l'échec de la réservation via WebHook Discord.
        Si WEBHOOK_URL est None, print juste le message
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
        logging.info(message)