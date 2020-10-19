#!/usr/bin/env /bin/bash

export PYTHONDONTWRITEBYTECODE=1

./wait-postgres.sh

if [ $# -eq 0 ]; then
  trap 'kill -TERM $PID' TERM INT
  KOMIDABOT_SKIP_INITIALISATION=true flask db upgrade
  PID=$!
  wait $PID
  trap - TERM INT
  wait $PID

  if [[ "$FLASK_ENV" = "production" ]]; then
      exec gunicorn --bind 0.0.0.0:5000 --log-level debug --workers 1 "app:create_app()"
  else
      exec python3 manage.py run -h 0.0.0.0
  fi
else
  echo "Running custom command:"
  echo "$@"
  exec /usr/bin/env "$@"
fi
