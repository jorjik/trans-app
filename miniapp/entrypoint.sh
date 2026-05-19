#!/bin/sh
set -e

# Substitute PORT in nginx config
export PORT=${PORT:-80}
envsubst '${PORT}' < /etc/nginx/conf.d/default.conf > /tmp/default.conf
mv /tmp/default.conf /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g "daemon off;"
