#!/bin/bash
heroku maintenance:on --app ci-ascribe
git push staging master
heroku pg:backups restore `heroku pg:backups public-url --app=warm-hamlet-6893` DATABASE --app=ci-ascribe --confirm ci-ascribe
heroku features:disable -a ci-ascribe preboot
heroku run python manage.py migrate --remote staging
heroku features:enable -a ci-ascribe preboot
heroku maintenance:off --app ci-ascribe
