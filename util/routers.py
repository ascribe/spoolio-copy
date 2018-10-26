class CeleryTaskRouter(object):

    def route_for_task(self, task, args=None, kwargs=None):
        if task.startswith('emails.tasks') or task.startswith('web.art.email'):
            return {'exchange': 'emails',
                    'exchange_type': 'direct',
                    'routing_key': 'emails'}

        elif task.startswith('bitcoin.tasks'):
            return {'exchange': 'bitcoin',
                    'exchange_type': 'direct',
                    'routing_key': 'bitcoin'}

        return {'exchange': 'celery',
                'exchange_type': 'direct',
                'routing_key': 'celery'}
