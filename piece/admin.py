from django.contrib import admin

from piece.models import *

class PieceAdmin(admin.ModelAdmin):
    pass

admin.site.register(Piece, PieceAdmin)

