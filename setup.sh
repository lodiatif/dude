#!/usr/bin/env bash

pip install -r requirements.txt

pd=`pwd`

export DUDE_DB="$pd/dudefile.db"
export DUDE_NAMESPACE="default"
export PYTHONPATH=$pd/
export DUDE_SLACK_HOST='localhost'
export DUDE_SLACK_PORT=4390
