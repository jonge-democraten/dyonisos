#!/bin/sh
virtualenv -p python3 env
. env/bin/activate
pip install -r requirements.txt
python create_local_settings.py
