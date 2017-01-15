[![Build Status](https://travis-ci.org/jonge-democraten/dyonisos.svg?branch=master)](https://travis-ci.org/jonge-democraten/dyonisos) [![Coverage Status](https://coveralls.io/repos/github/jonge-democraten/dyonisos/badge.svg?branch=tests)](https://coveralls.io/github/jonge-democraten/dyonisos?branch=tests) [![Dependency Status](https://gemnasium.com/jonge-democraten/dyonisos.svg)](https://gemnasium.com/jonge-democraten/dyonisos) 
About
=====
Dyonisos is a Django based web application that was developed for the
Jonge Democraten. The JD organized events with some regularity where
guests have to subscribe and sometimes pay for entry. This is what
Dyonisos was made for. It should be easy to create a form for an event,
easy for guests to subscribe and pay and easy for the organizers of the
event to see who is subscribed to what.

Quick install
============
1. `$ ./clean_env.sh`
1. `$ ./build_env.sh`
1. `$ source ./env/bin/activate`
1. `$ cp events/local_settings_example.py events/local_settings.py`
1. Modify `events/local_settings.py` with appropriate values for `SECRET_KEY` and `MOLLIE_KEY`.
1. `$ python manage.py migrate`
1. `$ python manage.py createsuperuser`
1. `$ python manage.py runserver`

### System dependencies
On Ubuntu, the following packages need to be installed before running `build_env.sh`,
- python3-dev
- libmysqlclient-dev

Special credits
===============
Mathijs Kleijnen: 
    Suggesting the name Dyonisos  
Jonge Democraten: 
    Supporting development
