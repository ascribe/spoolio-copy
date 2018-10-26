# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.django_db
def test_create_coa(edition):
    from ..models import CoaFile
    coa_file = CoaFile.objects.create(user=edition.user_registered,
                                      key='ascribe_spiral.png',
                                      edition=edition.pk)
    edition.coa = coa_file
    edition.save()
