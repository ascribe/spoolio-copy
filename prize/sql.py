from django.db import connection



def get_jury_count(prize_id, round_id):
    SQL = """
        WITH roles AS (
            SELECT
                user_id,
                (replace(role_str, '''', '"')::json->>'prize')::int as prize,
                (replace(role_str, '''', '"')::json->>'round')::int as round

            FROM
                users_role

            WHERE
                role_str LIKE '{%%'
        )

        SELECT count(*)
        FROM roles
        WHERE prize = %s
            AND round = %s
    """

    cursor = connection.cursor()
    cursor.execute(SQL, [prize_id, round_id])
    row = cursor.fetchone()
    cursor.close()
    return row[0]


def get_ratings_for_pieces(prize_id, round_id):
    SQL = """
        SELECT
            piece_piece.id,
            prize_pieceatprize.round,
            avg(note_note.note::float),
            count(note_note.note)

        FROM
            prize_pieceatprize
            INNER JOIN piece_piece
                ON (prize_pieceatprize.piece_id = piece_piece.id)
            INNER JOIN note_note
                ON (piece_piece.id = note_note.piece_id)

        WHERE
            prize_pieceatprize.prize_id = %s
            AND prize_pieceatprize.round = %s
            AND note_note.type LIKE 'Rating'
            AND note_note.note NOT LIKE ''

        GROUP BY
            piece_piece.id,
            prize_pieceatprize.round
    """

    cursor = connection.cursor()
    cursor.execute(SQL, [prize_id, round_id])
    l = cursor.fetchall()
    cursor.close()
    return l


def get_pieces(prize_id, round_id):
    SQL = """
        WITH user_role AS (
            SELECT
                user_id,
                (replace(role_str, '''', '"')::json->>'prize')::int as prize,
                (replace(role_str, '''', '"')::json->>'round')::int as round

            FROM
                users_role

            WHERE
                role_str LIKE '{%%'
        ),

        ratings AS (
            SELECT
                piece_piece.id piece_id,
                prize_pieceatprize.round,
                user_role.round user_round,
                avg(note_note.note::float) average,
                count(note_note.note) num_ratings

            FROM
                note_note
                INNER JOIN auth_user
                    ON (note_note.user_id = auth_user.id
                        AND note_note.type LIKE 'Rating'
                        AND note_note.note NOT LIKE '')
                INNER JOIN user_role
                    ON (auth_user.id = user_role.user_id AND
                        user_role.prize = %s AND
                        user_role.round = %s)
                INNER JOIN piece_piece
                    ON (note_note.piece_id = piece_piece.id)
                INNER JOIN prize_pieceatprize
                    ON (piece_piece.id = prize_pieceatprize.piece_id)

            GROUP BY
                piece_piece.id,
                prize_pieceatprize.round,
                user_role.round
        )

        SELECT
            piece_piece.id,
            piece_piece.title,
            piece_piece.artist_name,
            LPAD(users_role.id::text, 5, '0'),
            piece_piece.edition_number,
            piece_piece.num_editions,
            format('%%s, %%s/%%s',
                   EXTRACT(YEAR FROM piece_piece.datetime_registered),
                   piece_piece.edition_number, piece_piece.num_editions),
            piece_piece."bitcoin_id",
            blobs_thumbnail.thumbnail_file,
            ratings.average,
            ratings.num_ratings,
            prize_pieceatprize.round

        FROM
            piece_piece
            INNER JOIN prize_pieceatprize
                ON (prize_pieceatprize.piece_id = piece_piece.id AND
                    prize_pieceatprize.prize_id = %s AND
                    prize_pieceatprize.round >= %s)
            INNER JOIN users_role
                ON (users_role.user_id = piece_piece.owner_id)
            LEFT OUTER JOIN blobs_thumbnail
                ON (blobs_thumbnail.id = piece_piece.thumbnail_id)
            LEFT OUTER JOIN ratings
                ON (piece_piece.id = ratings.piece_id AND
                    ratings.user_round = %s)
    """

    cursor = connection.cursor()
    cursor.execute(SQL, [prize_id, round_id, prize_id, round_id, round_id])
    l = cursor.fetchall()
    cursor.close()
    return l


def get_ratings_for_piece_detail(prize_id, round_id, piece_id):
    SQL = """
        WITH roles AS (
            SELECT
                user_id,
                (replace(role_str, '''', '"')::json->>'prize')::int as prize,
                (replace(role_str, '''', '"')::json->>'round')::int as round

            FROM
                users_role

            WHERE
                role_str LIKE '{%%'
        )

        SELECT
            auth_user.username,
            rating.note rating,
            note.note note

        FROM roles
            INNER JOIN auth_user
                ON (auth_user.id = roles.user_id)
            LEFT OUTER JOIN note_note note
                ON (roles.user_id = note.user_id
                    AND note.type LIKE 'Note'
                    AND note.piece_id = %s)
            LEFT OUTER JOIN note_note rating
                ON (roles.user_id = rating.user_id
                    AND rating.type LIKE 'Rating'
                    AND rating.piece_id = %s)

        WHERE prize = %s
            AND round = %s
    """

    cursor = connection.cursor()
    cursor.execute(SQL, [piece_id, piece_id, prize_id, round_id])
    l = list(cursor.fetchall())
    cursor.close()
    return l


def get_pieces_with_my_ratings(prize_id, round_id, user_id):
    SQL = """
        WITH ratings AS (
            SELECT
                piece_piece.id piece_id,
                note_note.note::float rating

            FROM
                note_note
                INNER JOIN piece_piece
                    ON (note_note.piece_id = piece_piece.id)
                INNER JOIN prize_pieceatprize
                    ON (piece_piece.id = prize_pieceatprize.piece_id)
            WHERE
                note_note.user_id = %s
                AND note_note.type LIKE 'Rating'
                AND note_note.note NOT LIKE ''
        )

        SELECT
            piece_piece.id,
            piece_piece.title,
            piece_piece.artist_name,
            LPAD(users_role.id::text, 5, '0'),
            piece_piece.edition_number,
            piece_piece.num_editions,
            format('%%s, %%s/%%s',
                   EXTRACT(YEAR FROM piece_piece.datetime_registered),
                   piece_piece.edition_number, piece_piece.num_editions),
            piece_piece."bitcoin_id",
            blobs_thumbnail.thumbnail_file,
            ratings.rating

        FROM
            piece_piece
            INNER JOIN prize_pieceatprize
                ON (prize_pieceatprize.piece_id = piece_piece.id AND
                    prize_pieceatprize.prize_id = %s AND
                    prize_pieceatprize.round >= %s)
            INNER JOIN users_role
                ON (users_role.user_id = piece_piece.owner_id)
            LEFT OUTER JOIN blobs_thumbnail
                ON (blobs_thumbnail.id = piece_piece.thumbnail_id)
            LEFT OUTER JOIN ratings
                ON (piece_piece.id = ratings.piece_id)
    """

    cursor = connection.cursor()
    cursor.execute(SQL, [user_id, prize_id, round_id])
    l = cursor.fetchall()
    cursor.close()
    return l

