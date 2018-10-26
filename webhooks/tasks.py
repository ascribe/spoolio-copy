import logging
from celery.exceptions import MaxRetriesExceededError
from celery.task import Task

import json
import requests

logger = logging.getLogger(__name__)


class DeliverHook(Task):

    max_retries = 2

    def run(self, target, payload, instance=None, hook=None, **kwargs):
        """
        target:     the url to receive the payload.
        payload:    a python primitive data structure
        instance:   a possibly null "trigger" instance
        hook:       the defining Hook object
        """
        try:
            requests.post(
                url=target,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
        except requests.ConnectionError:
            self.retry(countdown=60)
        except (MaxRetriesExceededError, Exception) as e:
            logging.warning(e.message)


deliver_hook_wrapper = DeliverHook.delay
