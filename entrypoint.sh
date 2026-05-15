#!/usr/bin/env bash
set -e

cd /app

if [ ! -f .env ]; then
  echo ".env not found, generating from environment variables"
  required_vars=(
    GRAYLOG_HOST
    GRAYLOG_TOKEN
    CLICKHOUSE_HOST
    CLICKHOUSE_PORT
    CLICKHOUSE_USERNAME
    CLICKHOUSE_PASSWORD
  )

  for var in "${required_vars[@]}"; do
    value="${!var}"
    if [ -n "$value" ]; then
      echo "$var=$value" >> .env
    else
      echo "Warning: $var is not set and will not be written to .env"
    fi
  done
fi

exec "$@"
