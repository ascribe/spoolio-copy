from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status

from note.models import PrivateNote, PublicNote
from note.serializers import NoteSerializer, PublicEditionNoteSerializer, NotePieceSerializer, PublicPieceNoteSerializer
from web.api_util import GenericViewSetKpi


class NoteEndpoint(GenericViewSetKpi):
    """
    Note API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = PrivateNote.objects.filter(edition__isnull=False)
    # When writing class based views there is no easy way to override the
    # permissions for invidual view methods. The easiest way is to
    # create custom permission classes
    permission_classes = [IsAuthenticatedOrReadOnly]
    json_name = 'notes'

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, self.json_name: serializer.data}, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        queryset = self.get_queryset()

        if serializer.is_valid():
            edition = serializer.validated_data['bitcoin_id']
            db_note = queryset.filter(user=request.user, edition=edition)
            db_note = db_note[0] if len(db_note) > 0 else None
            if not db_note:
                db_note = queryset.create(user=request.user,
                                          edition=edition,
                                          piece=edition.parent,
                                          note=serializer.validated_data['note'],
                                          type=queryset.model.__name__)
                db_note.save()
            else:
                db_note.note = serializer.validated_data['note']
                db_note.save()
            serializer = self.get_serializer(db_note)
            return Response({'success': True, self.json_name[:-1]: serializer.data}, status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        return NoteSerializer

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.filter(user=self.request.user)
        return self.queryset


class NotePieceEndpoint(NoteEndpoint):
    queryset = PrivateNote.objects.filter(edition=None)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        queryset = self.get_queryset()

        if serializer.is_valid():
            piece = serializer.validated_data['id']
            db_note = queryset.filter(user=request.user, piece=piece)
            db_note = db_note[0] if len(db_note) > 0 else None
            if not db_note:
                db_note = queryset.create(user=request.user,
                                          edition=None,
                                          piece=piece,
                                          note=serializer.validated_data['note'],
                                          type=queryset.model.__name__)
                db_note.save()
            else:
                db_note.note = serializer.validated_data['note']
                db_note.save()
            serializer = self.get_serializer(db_note)
            return Response({'success': True, self.json_name[:-1]: serializer.data}, status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        return NotePieceSerializer


class PublicEditionNoteEndpoint(NoteEndpoint):
    """
    PublicEditionNote API endpoint
    """
    queryset = PublicNote.objects.filter(edition__isnull=False)

    permission_classes = [IsAuthenticatedOrReadOnly]
    json_name = 'edition_notes'

    def get_serializer_class(self):
        if self.action == 'create':
            return PublicEditionNoteSerializer
        return NoteSerializer


class PublicPieceNoteEndpoint(NotePieceEndpoint):
    queryset = PublicNote.objects.filter(edition=None)

    permission_classes = [IsAuthenticatedOrReadOnly]
    json_name = 'piece_notes'

    def get_serializer_class(self):
        if self.action == 'create':
            return PublicPieceNoteSerializer
        return NotePieceSerializer
