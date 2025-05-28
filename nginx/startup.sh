#!/bin/sh

# Paths to the real and dummy certificates
REAL_CERT="/etc/letsencrypt/live/de-duke.com/fullchain.pem"
REAL_KEY="/etc/letsencrypt/live/de-duke.com/privkey.pem"
DUMMY_CERT="/etc/nginx/certs/dummy-cert.pem"
DUMMY_KEY="/etc/nginx/certs/dummy-key.pem"
NGINX_CONF="/etc/nginx/conf.d/default.conf"
UPDATED_CONF="/etc/nginx/conf.d/default-updated.conf"

# Check if the real certificate exists
if [ -f "$REAL_CERT" ] && [ -f "$REAL_KEY" ]; then
    echo "Using real SSL certificates."
    sed "s|$DUMMY_CERT|$REAL_CERT|g; s|$DUMMY_KEY|$REAL_KEY|g" $NGINX_CONF > $UPDATED_CONF
else
    echo "Using dummy SSL certificates."
    cp $NGINX_CONF $UPDATED_CONF
fi

# Point Nginx to the updated configuration
mv $UPDATED_CONF $NGINX_CONF

# Start Nginx
nginx -g "daemon off;"