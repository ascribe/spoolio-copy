
class APIUtilActionControl(object):

    PIECE_ACL_REGISTREE_BEFORE_EDITIONS = [
        ('acl_view', True),
        ('acl_edit', True),
        ('acl_download', True),
        ('acl_delete', True),
        ('acl_create_editions', True),
        ('acl_share', True),
        ('acl_unshare', False),
        ('acl_transfer', False),
        ('acl_withdraw_transfer', False),
        ('acl_consign', False),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', True),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_loan_request', False),
    ]

    PIECE_ACL_REGISTREE_AFTER_EDITIONS = [
        ('acl_view', True),
        ('acl_edit', True),
        ('acl_download', True),
        ('acl_delete', True),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', False),
        ('acl_transfer', False),
        ('acl_withdraw_transfer', False),
        ('acl_consign', False),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', True),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_loan_request', False),
    ]

    EDITION_ACL_REGISTREE = [
        ('acl_view', True),
        ('acl_edit', True),
        ('acl_download', True),
        ('acl_delete', True),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', False),
        ('acl_transfer', True),
        ('acl_withdraw_transfer', False),
        ('acl_consign', True),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', True),
        ('acl_coa', True),
        ('acl_view_editions', True),
        ('acl_loan_request', False),
    ]

    EDITION_ACL_REGISTREE_AFTER_DELETE = [
        ('acl_view', False),
        ('acl_edit', True),
        ('acl_download', True),
        ('acl_delete', True),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', False),
        ('acl_transfer', True),
        ('acl_withdraw_transfer', False),
        ('acl_consign', True),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', True),
        ('acl_coa', True),
        ('acl_view_editions', True),
        ('acl_loan_request', False),
    ]

    PIECE_ACL_SHAREE = [
        ('acl_view', True),
        ('acl_edit', False),
        ('acl_download', True),
        ('acl_delete', False),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', True),
        ('acl_transfer', False),
        ('acl_withdraw_transfer', False),
        ('acl_consign', False),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', False),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_loan_request', True),
    ]

    EDITION_ACL_TRANSFEREE = [
        ('acl_view', True),
        ('acl_edit', False),
        ('acl_download', True),
        ('acl_delete', True),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', False),
        ('acl_transfer', True),
        ('acl_withdraw_transfer', False),
        ('acl_consign', True),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', True),
        ('acl_coa', True),
        ('acl_view_editions', True),
        ('acl_loan_request', False),
    ]

    EDITION_ACL_PREV_OWNER = [
        ('acl_view', True),
        ('acl_edit', False),
        ('acl_download', True),
        ('acl_delete', False),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', True),
        ('acl_transfer', False),
        ('acl_withdraw_transfer', False),
        ('acl_consign', False),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', False),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_loan_request', False),
    ]

    EDITION_ACL_PREV_OWNER_USER_NEEDS_TO_REGISTER = [
        ('acl_view', True),
        ('acl_edit', False),
        ('acl_download', True),
        ('acl_delete', False),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', False),
        ('acl_transfer', False),
        ('acl_withdraw_transfer', True),
        ('acl_consign', False),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', False),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_loan_request', False),
    ]

    EDITION_ACL_CONSIGNEE = [
        ('acl_view', True),
        ('acl_edit', False),
        ('acl_download', True),
        ('acl_delete', False),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', False),
        ('acl_transfer', False),
        ('acl_withdraw_transfer', False),
        ('acl_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', False),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_withdraw_consign', False),
        ('acl_loan_request', False),
    ]

    EDITION_ACL_CONSIGN_OWNER = [
        ('acl_view', True),
        ('acl_edit', False),
        ('acl_download', True),
        ('acl_delete', False),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', False),
        ('acl_transfer', False),
        ('acl_withdraw_transfer', False),
        ('acl_consign', False),
        ('acl_withdraw_consign', True),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', False),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_loan_request', False),
    ]

    EDITION_ACL_CONSIGN_OWNER_AFTER_CONFIRM = [
        ('acl_view', True),
        ('acl_edit', False),
        ('acl_download', True),
        ('acl_delete', False),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', False),
        ('acl_transfer', False),
        ('acl_withdraw_transfer', False),
        ('acl_consign', False),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', True),
        ('acl_loan', False),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_loan_request', False),
    ]

    EDITION_ACL_CONSIGNEE_AFTER_CONFIRM = [
        ('acl_view', True),
        ('acl_edit', False),
        ('acl_download', True),
        ('acl_delete', False),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', False),
        ('acl_transfer', True),
        ('acl_withdraw_transfer', False),
        ('acl_consign', False),
        ('acl_unconsign', True),
        ('acl_request_unconsign', False),
        ('acl_loan', True),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_withdraw_consign', False),
        ('acl_loan_request', False),
    ]

    EDITION_ACL_SHAREE = [
        ('acl_view', True),
        ('acl_edit', False),
        ('acl_download', True),
        ('acl_delete', False),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', True),
        ('acl_transfer', False),
        ('acl_withdraw_transfer', False),
        ('acl_consign', False),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', False),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_loan_request', True),
    ]

    EDITION_ACL_SHAREE_AFTER_DELETE = [
        ('acl_view', False),
        ('acl_edit', False),
        ('acl_download', True),
        ('acl_delete', False),
        ('acl_create_editions', False),
        ('acl_share', True),
        ('acl_unshare', True),
        ('acl_transfer', False),
        ('acl_withdraw_transfer', False),
        ('acl_consign', False),
        ('acl_withdraw_consign', False),
        ('acl_unconsign', False),
        ('acl_request_unconsign', False),
        ('acl_loan', False),
        ('acl_coa', False),
        ('acl_view_editions', True),
        ('acl_loan_request', False),
    ]

    PIECE_ACL_SHAREE_AFTER_DELETE = EDITION_ACL_SHAREE_AFTER_DELETE

    def is_piece_registree_before_editions(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.PIECE_ACL_REGISTREE_BEFORE_EDITIONS)

    def is_piece_registree_after_editions(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.PIECE_ACL_REGISTREE_AFTER_EDITIONS)

    def is_edition_registree(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_REGISTREE)

    def is_edition_registree_after_delete(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_REGISTREE_AFTER_DELETE)

    def is_piece_sharee(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.PIECE_ACL_SHAREE)

    def is_edition_transferee(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_TRANSFEREE)

    def is_edition_prev_owner(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_PREV_OWNER)

    def is_edition_prev_owner_user_needs_to_register(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_PREV_OWNER_USER_NEEDS_TO_REGISTER)

    def is_edition_consignee(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_CONSIGNEE)

    def is_edition_consign_owner(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_CONSIGN_OWNER)

    def is_edition_consign_owner_after_confirm(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_CONSIGN_OWNER_AFTER_CONFIRM)

    def is_edition_consignee_after_confirm(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_CONSIGNEE_AFTER_CONFIRM)

    def is_edition_acl_sharee(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_SHAREE)

    def is_edition_acl_sharee_after_delete(self, acl):
        return self._acl_to_sorted_list(acl) == sorted(self.EDITION_ACL_SHAREE_AFTER_DELETE)

    def is_piece_acl_sharee_after_delete(self, acl):
        return self.is_edition_acl_sharee_after_delete(acl)

    @staticmethod
    def _acl_to_sorted_list(acl):
        return sorted([(k, v) for k, v in acl.__dict__.iteritems() if k.startswith('acl')])
