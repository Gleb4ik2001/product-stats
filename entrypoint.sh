#!/bin/sh

if [ "$POSTGRES_HOST" = "db" ]; then
    echo "Ожидание запуска PostgreSQL на $POSTGRES_HOST:$POSTGRES_PORT..."
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.5
    done
    echo "PostgreSQL доступен!"
fi

exec "$@"