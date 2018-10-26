# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

import pytest


pytestmark = pytest.mark.django_db

@pytest.mark.django_db
@pytest.mark.usefixtures('djroot_user')
def test_web_user_list_loans_piece(alice, bob, loan_piece):
    from ..api import LoanPieceEndpoint
    from ..models import LoanPiece
    from ..serializers import LoanPieceSerializer

    url = reverse('api:ownership:loanpiece-list')
    factory = APIRequestFactory()
    request = factory.get(url)
    force_authenticate(request, user=alice)
    view = LoanPieceEndpoint.as_view({'get': 'list'})
    response = view(request)

    assert response.status_code == status.HTTP_200_OK

