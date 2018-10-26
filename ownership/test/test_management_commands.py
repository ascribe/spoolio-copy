from django.core.management import call_command
from django.utils.six import StringIO

import pytest


@pytest.mark.django_db
def test_create_license(alice):
    from ownership.models import License
    license_data = {
        'name': 'license_name',
        'code': 'license_code',
        'organization': 'license_organization',
        'url': 'license_url'
    }

    # Make sure the license doesn't exist yet
    assert not License.objects.filter(name=license_data['name']).exists()

    out = StringIO()
    call_command(
        'createlicense',
        '-o{}'.format(license_data['organization']),
        '-n{}'.format(license_data['name']),
        '-c{}'.format(license_data['code']),
        '-u{}'.format(license_data['url']),
        stdout=out,
    )
    assert License.objects.filter(**license_data).count() == 1
