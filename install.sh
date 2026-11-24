#!/usr/bin/env bash
# Installs nginx + the demo web app on Debian/Ubuntu. Run as root from this folder:
#   sudo ./install.sh
set -euo pipefail
cd "$(dirname "$0")"

apt-get update
apt-get install -y nginx python3 python3-venv curl

# App user, code and virtualenv
id webapp &>/dev/null || useradd -r -s /usr/sbin/nologin webapp
mkdir -p /opt/webapp /var/log/webapp
cp app/app.py /opt/webapp/
python3 -m venv /opt/webapp/venv
/opt/webapp/venv/bin/pip install --quiet flask gunicorn
chown -R webapp:webapp /opt/webapp /var/log/webapp
chmod 755 /var/log/webapp

# systemd service
cp systemd/webapp.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now webapp

# nginx site
cp nginx/webapp.conf /etc/nginx/sites-available/webapp
ln -sf /etc/nginx/sites-available/webapp /etc/nginx/sites-enabled/webapp
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl reload nginx || systemctl restart nginx

sleep 2
curl -fsS http://127.0.0.1/health && echo
echo "Done. Logs:"
echo "  /var/log/nginx/webapp_access.log"
echo "  /var/log/nginx/webapp_error.log"
echo "  /var/log/webapp/app.log"
