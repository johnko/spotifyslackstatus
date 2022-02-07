#!/usr/bin/env bash
set -euo pipefail

echo -n "Input your SESSION_DYNAMODB_TABLE: "
read -r SESSION_DYNAMODB_TABLE
export SESSION_DYNAMODB_TABLE
echo $SESSION_DYNAMODB_TABLE


export AWS_REGION='ca-central-1'
export SESSION_DYNAMODB_REGION="$AWS_REGION"
export SPOTIPY_REDIRECT_URI='http://127.0.0.1:8080'
python3 app.py
