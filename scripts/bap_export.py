'''
Simple module to download all BAP-related files.

The script creates a directory structure similar to the follwing one:

```
BAP
  - Artist 1
    - Submission 1
      - file...
      - file...
      - file...

    - Submission 2
      - file...
      - file...
      - file...

  - Artist 2
    - Submission 1
      - file...

    - Submission 2
      - file...
      - file...
      - file...

    - Submission 3
      - file...
      - file...
      - file...
  ...
```
'''



import psycopg2
import psycopg2.extras
import psycopg2.extensions
import os
import errno
import itertools
import codecs
import shutil
from slugify import slugify


psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)


SRC = '/home/alberto/ascribe/ascribe0/'
DST = '/home/alberto/ascribe/bap/'

conn = psycopg2.connect(database='d97ec35n8a8u47',
                        user='ub6dc7a4vfln9i',
                        password='paqdtkggrc8gs07tmmfnutn0d49',
                        host='ec2-54-163-236-28.compute-1.amazonaws.com',
                        port=5482,
                        sslmode='require')

SQL_FROM = """
FROM
    django_piecemodel
    INNER JOIN django_pieceatprizemodel
        ON (django_pieceatprizemodel.piece = django_piecemodel.id)
    INNER JOIN django_roleatusermodel
        ON (django_roleatusermodel.user_id = django_piecemodel.owner_id)
    INNER JOIN auth_user
        ON (django_piecemodel.owner_id = auth_user.id)
    LEFT OUTER JOIN s3_digitalworkmodel
        ON (django_piecemodel.digital_work_model = s3_digitalworkmodel.id)
    LEFT OUTER JOIN s3_otherdatamodel
        ON (django_piecemodel.other_data_model = s3_otherdatamodel.id)

"""


SQL_COUNT = """
SELECT
    count(*)
""" + SQL_FROM


SQL_DATA = """
SELECT
    auth_user.username username,
    LPAD(django_roleatusermodel.id::text, 5, '0') artist_id,
    django_piecemodel.id piece_id,
    django_piecemodel.title piece_title,
    django_piecemodel."bitcoin_id" bitcoin_id,
    django_piecemodel.artist_name artist_name,
    django_pieceatprizemodel.extra_data extra,
    s3_digitalworkmodel.digital_work_file work_url,
    s3_otherdatamodel.other_data_file other_data_url
""" + SQL_FROM + """
ORDER BY
    auth_user.username,
    django_piecemodel.id
"""


def ensure_path(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def process_artist(r):
    artist_id, artist_name = r['artist_id'], r['artist_name']
    artist_dir = os.path.join(DST,
                              slugify(u' '.join([artist_id, artist_name])))
    return artist_dir


def process_work(artist_dir, i, r):
    # make destination path
    piece_id, piece_title = str(i + 1), r['piece_title']
    work_dir = os.path.join(artist_dir,
                            slugify(u' '.join([piece_id, piece_title])))

    ensure_path(work_dir)

    # unpack JSON data, sorry for the "eval"
    process_metadata(work_dir, r, eval(r['extra']))

    # copy assets
    work_url = r['work_url']
    if not work_url:
        return
    try:
        extension = os.path.splitext(work_url)[1]
    except AttributeError:
        extension = ''
    shutil.copy(os.path.join(SRC, work_url),
                os.path.join(work_dir, 'artwork' + extension))

    # copy other assets
    other_data_url = r['other_data_url']
    if other_data_url:
        extension = os.path.splitext(other_data_url)[1]
        shutil.copy(os.path.join(SRC, other_data_url),
                    os.path.join(work_dir, 'extra_content' + extension))



def process_metadata(work_dir, data, extra):
    TEMPLATE = u"""Artist data
===========

name:    {artist_name}
email:   {username}
phone:   {bap_phone}
address: {bap_street}, {bap_city}
applied for residency: {bap_residency}



Artwork data
============

title:        {piece_title}
medium:       {bap_medium}
measurements: {bap_measurements}
insurance:    {bap_insurance}
url:          https://www.ascribe.io/art/piece/{bitcoin_id}
databank:     {bap_databank}



Artwork description
===================
{bap_description}



Artist statement
================
{bap_artist_statement}

"""

    merged_data = data.copy()
    merged_data.update(extra)
    merged_data['bap_residency'] = 'Yes' if extra['bap_residency'] else 'No'

    if not merged_data['bap_description']:
        merged_data['bap_description'] = 'n/a'

    if not merged_data['bap_artist_statement']:
        merged_data['bap_artist_statement'] = 'n/a'

    with codecs.open(os.path.join(work_dir, 'info.txt'), 'w') as f:
        f.write(TEMPLATE.format(**merged_data).encode('utf-8'))


def main():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(SQL_COUNT)
    total = cur.fetchone()['count']

    cur.execute(SQL_DATA)
    for key, row in itertools.groupby(cur, lambda x: x['username']):
        artist_dir = None
        for i, r in enumerate(row):
            if not artist_dir:
                artist_dir = process_artist(r)
            process_work(artist_dir, i, r)
            total -= 1
            print total



if __name__ == '__main__':
    main()

