from rest_framework import routers

from ownership import api as ownership_api
from acl import api as acl_api


router = routers.DefaultRouter()
router.register(r'/registrations', ownership_api.RegistrationEndpoint)
router.register(r'/transfers', ownership_api.TransferEndpoint)
router.register(r'/consigns', ownership_api.ConsignEndpoint)
router.register(r'/unconsigns', ownership_api.UnConsignEndpoint)
router.register(r'/contracts', ownership_api.ContractEndpoint, 'contract')
router.register(r'/contract_agreements',
                ownership_api.ContractAgreementEndpoint,
                'contractagreement')
router.register(r'/loans/editions', ownership_api.LoanEndpoint)
router.register(r'/loans/pieces', ownership_api.LoanPieceEndpoint)
router.register(r'/shares/editions', ownership_api.ShareEndpoint)
router.register(r'/licenses', ownership_api.LicenseEndpoint)
router.register(r'/shares/pieces', ownership_api.SharePieceEndpoint)
router.register(r'/acls', acl_api.ActionControlEndpoint)
urlpatterns = router.urls
