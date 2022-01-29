#!/usr/bin/env bash
set -euo pipefail

echo -n "Input your SPOTIFY_CLIENT_ID: "
read -r SPOTIPY_CLIENT_ID
export SPOTIPY_CLIENT_ID
echo $SPOTIPY_CLIENT_ID

echo -n "Input your SPOTIFY_CLIENT_SECRET: "
read -r SPOTIPY_CLIENT_SECRET
export SPOTIPY_CLIENT_SECRET
echo $SPOTIPY_CLIENT_SECRET

echo -n "Input your SLACK_CLIENT_ID: "
read -r SLACK_CLIENT_ID
export SLACK_CLIENT_ID
echo $SLACK_CLIENT_ID

echo -n "Input your SLACK_CLIENT_SECRET: "
read -r SLACK_CLIENT_SECRET
export SLACK_CLIENT_SECRET
echo $SLACK_CLIENT_SECRET

export SPOTIPY_REDIRECT_URI='http://127.0.0.1:8080'
python3 app.py
