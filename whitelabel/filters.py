import django_filters
from piece.models import Piece


class SubmittedPieceFilter(django_filters.FilterSet):
    # always provide with inheritance!
    user_submitted_to = None
    submitted = django_filters.MethodFilter(action='filter_submitted')
    accepted = django_filters.MethodFilter(action='filter_accepted')

    def __init__(self, user_submitted_to, *args, **kwargs):
        self.user_submitted_to = user_submitted_to

        super(SubmittedPieceFilter, self).__init__(*args, **kwargs)

    class Meta:
        model = Piece
        fields = ('artist_name', 'title', 'submitted', 'accepted')

    def filter_submitted(self, qs, value):
        return self._filter_submitted_loans(qs, value, ownership_at_piece__status=None)

    def filter_accepted(self, qs, value):
        return self._filter_submitted_loans(qs, value, ownership_at_piece__status=1)

    def _filter_submitted_loans(self, qs, value, **kwargs):
        if value in ('true', True):
            return qs.filter(ownership_at_piece__new_owner=self.user_submitted_to,
                             ownership_at_piece__type="LoanPiece",
                             ownership_at_piece__datetime_deleted=None,
                             **kwargs)
        else:
            return qs.exclude(ownership_at_piece__new_owner=self.user_submitted_to,
                              ownership_at_piece__type="LoanPiece",
                              ownership_at_piece__datetime_deleted=None,
                              **kwargs)