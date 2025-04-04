## Bonjour !
Le SUAPS (service sports de Nantes Université) propose des créneaux horaires pour faire du sport, cependant ces créneaux sont très vite remplis.
J'ai donc fait un petit programme qui permet de réserver des créneaux sans s'embêter à se connecter à son compte, etc.

Tout se fait avec des requêtes GET/POST. J'ai utilisé [Burp Suite](https://portswigger.net/burp/releases/professional-community-2024-8-5?requestededition=community&requestedplatform=). C'est un outil qui permet d'intercepter les requêtes, voir leur contenu, etc. Cela m'a permis de savoir à quels URLs GET, et quel contenu. Cela m'a aussi aidé pour savoir quelle data JSON il fallait POST pour résever un créneau, ce qui m'a permis de reconstruire le JSON et de réussir la requête POST.

Tout ce dont vous aurez besoin, c'est de votre username et password, et je suppose qu'il faut que vous ayez adhéré au SUAPS.


### Fonctionnement
On fait tourner le programme une première fois pour récupérer les IDs des créneaux qu'on veut réserver de manière automatique. Ensuite, on les place dans config.json et on laisse le programme faire !

### Ce que vous devez faire
- Cloner le dépot :
    ```bash
    git clone https://github.com/flash2974/reserverCreneauSUAPS && cd reserverCreneauSUAPS/
    ```
- Dans `config/` renommer `.example.env` en `.env`, et `example.config.json` en `config.json` (1) : 
    ```bash
    mv config/.example.env config/.env && mv config/example.config.json config/config.json
    ```

- Ouvrir le fichier `.env` et remplir les champs **USERNAME** et **PASSWORD**
    ```bash
    echo -e "USERNAME=username\nPASSWORD=mdp" > config/.env
    ```

#### Avec Docker (`http`):
```bash
docker compose up -d
```
- Visiter [**http://localhost:5000**](http://localhost:5000): il vous suffira de cocher les **activités** qui vous intéressent et de sauvegarder. Les horaires d'activation du bot sont automatiquement définies.
- Pour mettre à jour le container:

    ```bash
    docker compose down && \
    docker rmi reservercreneausuaps-app && \
    git pull && \
    docker compose up -d --build
    ```

#### Avec Docker (`https`):
```bash
cp example.docker-compose-v2.yml docker-compose-v2.yml && cp config/example.traefik-config.yml config/traefik-config.yml 
```
```bash
mkdir -p ~/docker/traefik/ && touch ~/docker/traefik/acme.json && chmod 600 ~/docker/traefik/acme.json
``` 
- Dans `config/traefik-config.yml`, remplacer **EMAIL** avec votre **email**
- Dans `docker-compose-v2.yml` remplacer **DOMAIN** avec votre nom de **domaine** / **sous domaine**
```bash
docker compose -p reservercreneausuaps --file docker-compose-v2.yml up -d
```

<br>

Ensuite, vous aurez accès à la *WebUI*. Dans un navigateur, allez à l'adresse de votre serveur (IP ou nom de domaine) et mettez vous sur le port 5000. Il faut au préalabale que le port soit ouvert.
Par exemple : 
`https://IP_de_mon_serveur:5000`

Connectez-vous sur la WebUI à l'aide de votre mot de passe universitaire (celui enregistré dans le .env)
Sélectionnez les créneaux que vous voulez réserver automatiquement et cliquez sur le bouton **Sauvegarder**

### TODO :
- fix `setIdPeriode()` dans `Fonctions.py` qui fixe le mauvais ID de période une semaine avant la période "spéciale" (Noël)
- limiter le nombre d'activités sélectionnables dans la web_ui

<br>
<br>

(1) Si vous voulez faire des pulls requests, copiez et renommez.
```bash
cp config/.example.env config/.env && cp config/example.config.json config/config.json
```

<br>

Merci à [maxlttr](https://github.com/maxlttr1) pour son aide !
