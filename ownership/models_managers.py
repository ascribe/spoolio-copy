from django.db import models


class OwnershipRegistrationManager(models.Manager):
    """ Manager for OwnershipRegistration """

    def get_queryset(self):
        return super(OwnershipRegistrationManager, self).get_queryset().filter(type='OwnershipRegistration')


class OwnershipEditionsManager(models.Manager):
    """ Manager for OwnershipRegistration """

    def get_queryset(self):
        return super(OwnershipEditionsManager, self).get_queryset().filter(type='OwnershipEditions')


class OwnershipPieceManager(models.Manager):
    def get_queryset(self):
        return super(OwnershipPieceManager, self).get_queryset().filter(type='OwnershipPiece')


class ConsignedRegistrationManager(models.Manager):
    """ Manager for ConsignedRegistration """

    def get_queryset(self):
        return super(ConsignedRegistrationManager, self).get_queryset().filter(type='ConsignedRegistration')


class OwnershipMigrationManager(models.Manager):
    """ Manager for OwnershipMigration """

    def get_queryset(self):
        return super(OwnershipMigrationManager, self).get_queryset().filter(type='OwnershipMigration')


class OwnershipTransferManager(models.Manager):
    """ Manager for OwnershipTransfer """

    def get_queryset(self):
        return super(OwnershipTransferManager, self).get_queryset().filter(type='OwnershipTransfer')


class ConsignmentManager(models.Manager):
    """ Manager for Consignment """

    def get_queryset(self):
        return super(ConsignmentManager, self).get_queryset().filter(type='Consignment')


class UnConsignmentManager(models.Manager):
    """ Manager for UnConsignment """

    def get_queryset(self):
        return super(UnConsignmentManager, self).get_queryset().filter(type='UnConsignment')


class LoanManager(models.Manager):
    """ Manager for Loan """

    def get_queryset(self):
        return super(LoanManager, self).get_queryset().filter(type='Loan')


class LoanPieceManager(models.Manager):
    """ Manager for LoanPiece """

    def get_queryset(self):
        return super(LoanPieceManager, self).get_queryset().filter(type='LoanPiece')


class ShareManager(models.Manager):
    """ Manager for Share """

    def get_queryset(self):
        return super(ShareManager, self).get_queryset().filter(type='Share')


class SharePieceManager(models.Manager):
    """ Manager for SharePiece """

    def get_queryset(self):
        return super(SharePieceManager, self).get_queryset().filter(type='SharePiece')
