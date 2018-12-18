#!/bin/bash
#
# Start the server as a service.
# This also takes care of stopping the existing service.
#

set -e

install="$1"
here="`dirname \"$0\"`"
pid_file="$here/service.pid"
output="$here/service.log"

cd "$here"
./stop.sh
if [ -n "$install" ]; then
  ./install.sh
fi

(
  cd ..
  source ENV/bin/activate
  if [ -f "$pid_file" ]; then
    >&2 echo "ERROR: Process is file $pid_file exists. Aborting."
    exit 1
  fi

  python3 app.py 2>"$output" 1>"$output" &
  pid="$!"
  echo "$pid" > "$pid_file"
  sleep 0.5
  if ! ps | grep -qE "(^|\s)$pid\s"; then
    >&2 echo "ERROR: Service exited during start."
    >&2 cat "$output"
    exit 2
  fi
)

