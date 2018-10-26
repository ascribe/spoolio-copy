import json
from celery.task import task


from coa.forms import VerifyCoaForm
from coa.models import create
from util.crypto import import_env_key, verify

from web.api_util import json_api


@task
@json_api
def create_coa(request):
    """
    """
    data = json.loads(request.body)
    create(request.user.username, data['bitcoin_id'])
    return


@json_api
def verify_coa(request):
    """
    """
    form = VerifyCoaForm(request.POST or None)
    assert form.is_valid(), form.errors.values()[0][0]
    priv_key = import_env_key('COA_PRIVKEY_1')
    signature = form.cleaned_data['signature'].replace(" ", "").replace("\r", "").replace("\n", "")
    try:
        verdict = verify(priv_key.publickey(), form.cleaned_data['message'], signature)
    except:
        verdict = False
    return {'verdict': verdict}

