
Lancer serveur : 
Avec fastapi (port 8000 obligé)
```
python -m fastapi run main.py
```

avec uvicorn (port 5000) :
```
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 5000
```


ancien truc :
# Requêtes du serveur :
/!\ Dans toutes les requetes, inclure un champ 'Token' dans le header, donc en json -> {'Token' : TOKEN}

## Infos sur activités
```
GET /api/activities
```
retourne infos sur toutes les activies + config (ids a resa) + sports réservés pr la semaine pro


## Réserver une activité (réservation instant)
```
POST /api/reserver
```

data dans la requete : dico avec un champ 'id_creneau_a_resa' avec 1 seul id à reserver :
ex : 
```py
{'id_creneau_a_resa' : 'ad7deded7e7d'}
```


## Modification config file (pour résa récurrentes)
```
POST /api/update
```

data dans la requete : ids (liste) des créneaux à résa ttes les semaines
```py
{'ids' : ['ad7deded7e7d', 'dddsd7854']}
```