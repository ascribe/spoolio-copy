# Copy production database to staging
#heroku pgbackups:capture --expire --app=warm-hamlet-6893
heroku pg:backups restore `heroku pg:backups public-url --app=warm-hamlet-6893` DATABASE --app=ci-ascribe --confirm ci-ascribe
