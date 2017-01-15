#!/bin/sh
virtualenv -p python3 env
source env/bin/activate
pip install -r requirements.txt
python manage.py create_local_settings.py
