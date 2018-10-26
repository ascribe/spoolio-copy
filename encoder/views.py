from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import json


__author__ = 'dimi'

@csrf_exempt
def notifications_handler(request):
    print json.loads(request.body)['job']['state']
    print json.loads(request.body)['job']['id']
    return HttpResponse("OK")