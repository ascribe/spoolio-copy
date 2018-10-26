#!/bin/bash
heroku maintenance:on --app=warm-hamlet-6893
git push live master
heroku features:disable -a warm-hamlet-6893 preboot
heroku run python manage.py migrate --remote live
heroku features:enable -a warm-hamlet-6893 preboot
heroku maintenance:off --app=warm-hamlet-6893
