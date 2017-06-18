#!/usr/bin/env bash

pip install -r requirements.txt

pd=`pwd`

export DUDE_DB="$pd/dude.db"
export PYTHONPATH=$pd/
export DUDE_SLACK_HOST='localhost'
export DUDE_SLACK_PORT=4390

mv $pd/dude.tmpl.db $DUDE_DB
