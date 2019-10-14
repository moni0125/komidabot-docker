#!/bin/bash

echo "Waiting for postgres..."

# Wait for the database in a safe manner
while :
do
    trap 'kill -TERM $PID' TERM INT
    nc -w 2 -z $POSTGRES_HOST 5432 &
    PID=$!
    wait $PID
    trap - TERM INT
    wait $PID
    EXIT_STATUS=$?

    if [[ ${EXIT_STATUS} -eq 0 ]]
    then
        break
    fi

    sleep 0.1
done

echo "PostgreSQL started"

trap 'kill -TERM $PID' TERM INT
KOMIDABOT_SKIP_INITIALISATION=true FLASK_APP=komidabot_app.py flask db upgrade
PID=$!
wait $PID
trap - TERM INT
wait $PID

exec python3 manage.py run -h 0.0.0.0
