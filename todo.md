## 🔄 1. **Désactiver Caddy **
Si Caddy tourne encore :
```bash
sudo systemctl stop caddy
sudo systemctl disable caddy
```

### 2. **Installer Apache**
```bash
sudo apt update
sudo apt install apache2
```

### 3. **Activer les modules nécessaires**
```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod ssl
sudo a2enmod headers
```
Puis redémarrer Apache :
```bash
sudo systemctl restart apache2
```

---

## 🔐 4. **Obtenir un certificat SSL avec Let's Encrypt**
Certificat SSL
```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d [nom de domaine]
```

---

## 🧾 5. **Configurer ton VirtualHost HTTPS**
Config apache :

```apache
<VirtualHost *:443>
    ServerName [nom de domaine]
    ServerAlias *.[nom de domaine]
    ServerAdmin [email]

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/[nom de domaine]/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/[nom de domaine]/privkey.pem

    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "DENY"
    Header always set X-XSS-Protection "1; mode=block"

    ProxyPreserveHost On
    ProxyPass /suaps http://localhost:5000/
    ProxyPassReverse /suaps http://localhost:5000/

    ErrorLog ${APACHE_LOG_DIR}/apache_revProxy_error.log
    CustomLog ${APACHE_LOG_DIR}/apache_revProxy_access.log combined
</VirtualHost>
```

Placer ce fichier dans `/etc/apache2/sites-available/reverse_proxy.conf`, puis l'activer :
```bash
sudo a2ensite reverse_proxy.conf
sudo systemctl reload apache2
```