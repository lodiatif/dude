#!/usr/bin/env bash

pip install -r requirements.txt

pd=`pwd`

export DUDE_NAMESPACE="default"
export PYTHONPATH=$pd/
export DUDE_SLACK_HOST='localhost'
export DUDE_SLACK_PORT=4390

export DUDE_STORE="file"

export DUDE_FILE_DB="$pd/dudefile.db"

export DUDE_MDB_URI="mongodb://localhost:27017/"
export DUDE_MDB_NAME="dude"
export DUDE_MDB_COLLECTION="secrets"
