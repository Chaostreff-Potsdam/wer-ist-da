#!/bin/bash
#
# Install what the service needs.
#

set -e

cd "`dirname \"$0\"`"
cd ..

command="sudo apt-get install python3 virtualenv"

echo "Checking Python 3"
if ! which python3; then
  echo "ERROR: Python 3 needs to be installed. "
  echo "  $command"
  exit 1
else
  echo "ok"
fi

echo "Checking virtualenv"
if ! which virtualenv; then
  echo "ERROR: virtualenv needs to be installed. "
  echo "  $command"
  exit 1
else
  echo "ok"
fi


if ! [ -d "ENV" ]; then
  virtualenv -p python3 ENV
fi

source ENV/bin/activate

git pull
pip install --upgrade -r requirements.txt


