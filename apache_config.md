
# Configu du reverse proxy
<VirtualHost *:443>
    ServerName flash2974.duckdns.org
    ServerAlias *.flash2974.duckdns.org
    ServerAdmin nathan_domenichini@yahoo.com

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/flash2974.duckdns.org/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/flash2974.duckdns.org/privkey.pem

    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "DENY"
    Header always set X-XSS-Protection "1; mode=block"

    ProxyPreserveHost On
    ProxyPass /suaps http://localhost:5000/
    ProxyPassReverse /suaps http://localhost:5000/

    ErrorLog ${APACHE_LOG_DIR}/flash2974_error.log
    CustomLog ${APACHE_LOG_DIR}/flash2974_access.log combined
</VirtualHost>
