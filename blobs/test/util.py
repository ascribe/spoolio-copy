from __future__ import absolute_import

from blobs.models import DigitalWork, Thumbnail, OtherData


class APIUtilDigitalWork(object):
    @staticmethod
    def create_digitalwork(user, amount=1,
                           digital_work_file='test/testuser/ascribe_spiral/digitalwork/ascribe_spiral.png'):
        if amount == 1:
            digital_work = DigitalWork(user=user, digital_work_file=digital_work_file)
            digital_work.save()
            return digital_work
        else:
            digital_works = [DigitalWork(user=user, digital_work_file=digital_work_file) for i in range(amount)]
            [d.save() for d in digital_works]
            return digital_works


class APIUtilThumbnail(object):
    @staticmethod
    def create_thumbnail(user, amount=1, thumbnail_file='test/testuser/ascribe_spiral/digitalwork/ascribe_spiral.png'):
        if amount == 1:
            thumbnail = Thumbnail(user=user, thumbnail_file=thumbnail_file)
            thumbnail.save()
            return thumbnail
        else:
            thumbnails = [Thumbnail(user=user, thumbnail_file=thumbnail_file) for i in range(amount)]
            [t.save() for t in thumbnails]
            return thumbnails


class APIUtilOtherData(object):
    @staticmethod
    def create_otherdata(user, amount=1, other_data_file='test/testuser/ascribe_spiral/digitalwork/ascribe_spiral.png'):
        other_data = [OtherData(user=user, other_data_file=other_data_file) for i in range(amount)]
        [o.save() for o in other_data]
        return other_data[0] if amount == 1 else other_data


class APIUtilContractBlobs(object):
    @staticmethod
    def create_contract(user, amount=1, other_data_file='test/testuser/ascribe_spiral/digitalwork/ascribe_spiral.png'):
        other_data = [OtherData(user=user, other_data_file=other_data_file) for i in range(amount)]
        [o.save() for o in other_data]
        return other_data[0] if amount == 1 else other_data
