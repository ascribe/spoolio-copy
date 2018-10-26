#!/bin/bash
python manage.py loaddata ownership/fixtures/licenses.json
python manage.py migrate
