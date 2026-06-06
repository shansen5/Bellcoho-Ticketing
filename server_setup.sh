#!/bin/bash
# Run this ONCE on the server: ssh root@159.223.153.249 'bash -s' < server_setup.sh
set -euo pipefail

APP_DIR="/var/www/ticketing2"
SERVICE="ticketing2"
ENV_FILE="/etc/$SERVICE.env"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

echo "==> Installing packages..."
apt-get update -q
apt-get install -y python3-pip python3-venv nginx

echo "==> Creating app directory structure..."
mkdir -p "$APP_DIR"/{static/uploads/photos,static/uploads/documents,instance}

echo "==> Creating Python venv..."
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip -q
"$APP_DIR/venv/bin/pip" install gunicorn -q

echo "==> Saving environment config to $ENV_FILE..."
cat > "$ENV_FILE" <<EOF
FLASK_APP=app.py
SECRET_KEY=$SECRET_KEY
EOF
chmod 600 "$ENV_FILE"

echo "==> Creating systemd service..."
cat > "/etc/systemd/system/$SERVICE.service" <<EOF
[Unit]
Description=ticketing2 gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 2 --bind unix:/run/$SERVICE/$SERVICE.sock -m 007 "app:create_app()"
RuntimeDirectory=$SERVICE
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE"

echo "==> Configuring nginx..."
cat > "/etc/nginx/sites-available/$SERVICE" <<'NGINX'
server {
    listen 80;
    server_name _;

    client_max_body_size 16M;

    location /static/ {
        alias /var/www/ticketing2/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://unix:/run/ticketing2/ticketing2.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
NGINX

ln -sf "/etc/nginx/sites-available/$SERVICE" "/etc/nginx/sites-enabled/"
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "==> Setting permissions..."
chown -R www-data:www-data "$APP_DIR"

echo ""
echo "======================================================"
echo "Server setup complete."
echo "SECRET_KEY saved to $ENV_FILE (chmod 600)."
echo ""
echo "Next steps:"
echo "  1. From your local machine:  ./deploy.sh"
echo "  2. Back on this server, initialize the database:"
echo "     cd $APP_DIR && set -a && source $ENV_FILE && set +a && venv/bin/flask init-db"
echo "======================================================"
