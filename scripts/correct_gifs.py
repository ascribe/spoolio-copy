__author__ = 'cevo'
from blobs.models import DigitalWork, Thumbnail
from piece.models import Piece
import sys, traceback

test_users = [22, 136, 118]

gifs = [d for d in DigitalWork.objects.all() if d and d.user_id and d.user_id not in test_users and '.gif' in d.digital_work_file]
#gifs = DigitalWork.objects.filter(user__isnull=False, digital_work_file__contains='.gif').exclude(user__pk__in=test_users)

thumbs = [t for t in Thumbnail.objects.all() if t and t.user_id and t.user_id not in test_users and '.gif' in t.thumbnail_file]
#thumbs = Thumbnail.objects.filter(user__isnull=False, thumbnail_file__contains='.gif').exclude(user__pk__in=test_users)
thumb_ids = [t.id for t in thumbs]

#pieces = [p.id for p in Piece.objects.filter(thumbnail__in=thumb_ids)]

#Piece.objects.filter(id__in=pieces).update(thumbnail_id='NULL')
Thumbnail.objects.filter(id__in=thumb_ids).delete()

new_thumbnails = []
bad_thumbnails = []

for g in gifs:
    basename = g.associated_key('thumbnail', '', unique=False)
    try:
        new_thumbnails.append(Thumbnail.thumbnail_from_url(g.user, g.url, basename))
    except Exception as e:
        print sys.exc_info()
        print traceback.print_exc()
        bad_thumbnails.append([sys.exc_info(), g])

print 'new thumbnails'
print new_thumbnails
print 'bad ones .. '
print bad_thumbnails

#for n in new_thumbnails:
#    piece_name = n.thumbnail_file.split('/')[2]
#    for g in gifs:
#        if piece_name in g.digital_work_file:
#            Piece.objects.filter(digital_work_id=g.id).update(thumbnail_id=n.id)
