#!/bin/bash

# Set default env vars if not defined
SERVER_NAME=${SERVER_NAME:-"Default"}
WORLD_NAME=${WORLD_NAME:-"Default"}
SERVER_PASS=${SERVER_PASS:-"password"}
PUBLIC=${PUBLIC:-1}
PORT=${PORT:-2456}

export templdpath=$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=./linux64:$LD_LIBRARY_PATH
export SteamAppId=892970

echo "Starting Valheim server: $SERVER_NAME"
./valheim_server.x86_64 -nographics -batchmode \
    -name "$SERVER_NAME" \
    -port $PORT \
    -world "$WORLD_NAME" \
    -password "$SERVER_PASS" \
    -public $PUBLIC

export LD_LIBRARY_PATH=$templdpath
