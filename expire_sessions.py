from django.contrib.sessions.models import Session
from django.utils.timezone import now


def expire_sessions():
    sessions = Session.objects.filter(expire_date__gt=now())
    for s in sessions:
        print 'logging out session with key {}'.format(s.session_key)
        s.expire_date = now()
        s.save()
