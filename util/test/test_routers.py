# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.parametrize('queue', ('emails', 'bitcoin', 'celery'))
def test_celery_task_router(queue):
    from ..routers import CeleryTaskRouter
    router = CeleryTaskRouter()
    route = router.route_for_task('{}.tasks.xyz'.format(queue))
    assert route['exchange'] == queue
    assert route['exchange_type'] == 'direct'
    assert route['routing_key'] == queue
