from __future__ import absolute_import

import os

from celery import Celery

from django.conf import settings

__author__ = 'dimi'

# TODO is this really needed?
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')

DEFAULT_AMQP = os.environ.get('CELERY_BROKER_URL',
                              'amqp://guest:guest@localhost//')

# # Celery app configuration
# app = Celery("tasks", backend=settings.DATABASE_URL.replace("postgres://", "db+postgresql://"),
#              broker=)
# import pdb; pdb.set_trace()
app = Celery('util',
             broker=os.environ.get("CLOUDAMQP_URL", DEFAULT_AMQP),
             include=['encoder.zencoder_api', 'prize.api',
                      'bitcoin.management.commands.import_addresses',
                      'bitcoin.management.commands.rescan_blockchain',
                      'bitcoin.management.commands.wallet_status',
                      'bitcoin.management.commands.clean_transactions',
                      'bitcoin.management.commands.refill'])

app.conf.update(
    CELERY_TASK_SERIALIZER=settings.CELERY_TASK_SERIALIZER,
    CELERY_ACCEPT_CONTENT=settings.CELERY_ACCEPT_CONTENT,  # Ignore other content
    CELERY_RESULT_SERIALIZER=settings.CELERY_RESULT_SERIALIZER,
    CELERY_TIMEZONE=settings.CELERY_TIMEZONE,
    CELERY_ENABLE_UTC=settings.CELERY_ENABLE_UTC,
    CELERY_TASK_RESULT_EXPIRES=settings.CELERY_TASK_RESULT_EXPIRES,
    BROKER_POOL_LIMIT=settings.BROKER_POOL_LIMIT,
    CELERYBEAT_SCHEDULER=settings.CELERYBEAT_SCHEDULER,
    BROKER_CONNECTION_TIMEOUT=30,  # May require a long timeout due to Linux DNS timeouts etc
    BROKER_HEARTBEAT=30,  # Will detect stale connections faster
    CELERY_SEND_EVENTS=False,  # Will not create celeryev.* queues
    CELERY_EVENT_QUEUE_EXPIRES=60,  # Will delete all celeryev. queues without consumers after 1 minute.
)

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

CELERY_TIMEZONE = 'UTC'


if __name__ == '__main__':
    app.start()
    print 'Celery up and running'
