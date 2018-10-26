from django.utils import timezone

__author__ = 'dimi'


def _uniqueHierarchicalString():
    """
    @return -- e.g. '2014/2/23/15/26/8/9877978'
    The last part (microsecond) is needed to avoid duplicates in rapid-fire
    transactions e.g. >1 edition

    """
    t = timezone.now()
    return '%s/%s/%s/%s/%s/%s/%s' % (
        t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond)
