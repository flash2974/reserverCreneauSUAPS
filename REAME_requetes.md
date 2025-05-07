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