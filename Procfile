web: newrelic-admin run-program gunicorn web.wsgi
celery: newrelic-admin run-program celery -A util worker -Q celery -n celery.%h -l info --without-gossip --without-heartbeat
emails: newrelic-admin run-program celery -A util worker -Q emails -n emails.%h -l info --without-gossip --without-heartbeat
bitcoin: celery -A util worker -Q bitcoin -n bitcoin.%h -l info --without-gossip --without-heartbeat
beat: newrelic-admin run-program celery -A util beat -l info
