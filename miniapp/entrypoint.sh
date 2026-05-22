#!/bin/sh
set -e

# Set defaults
export PORT=${PORT:-80}
export API_TARGET=${API_TARGET:-http://api:8000}

# Substitute variables in nginx config
envsubst '${PORT} ${API_TARGET}' < /etc/nginx/conf.d/default.conf > /tmp/default.conf
mv /tmp/default.conf /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g "daemon off;"
