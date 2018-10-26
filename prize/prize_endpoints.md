# Prize Endpoints

In this document we're enumerating through the different steps of the jury creation and rating of an piece.
We start at the beginning and list relevant endpoints

## Jury creation/invitation
Internally, jury members are normal ascribe users. To circumvent email enumeration vulnerabilities, an admin user can only invite by email without an auto completion at this point.

Endpoint: ```GET /api/prizes/<prize_name>/jury/```

Payload:
```
// gives back a list of jury member's email addresses (and their invitation status)
[
    {
        email: 'jury@member.com',
        status: 'invitation pending'
    },
    {
        email: 'jury2@member.com',
        status: 'invitation completed'
    },
]
```

Endpoint: ```POST /api/prizes/<prize_name>/jury/```

Payload:
```
// takes a jury member's email address
{
    email: 'jury@member.com'
}
```

Once an invitation is sent to a jury member's email there are two flows:

1. Jury member is not yet an ascribe user. An account needs to be created (user has to insert email address)
2. Jury member is an ascribe user. We can just redirect him to a piece overview view

Endpoint: ```DELETE /api/prizes/<prize_name>/jury/<email>/```

Deactivates the juror and makes all his votes inactive.

Endpoint: ```POST /api/prizes/<prize_name>/jury/<email>/activate/```

Activates the juror and makes all his votes active.

Endpoint: ```POST /api/prizes/<prize_name>/jury/<email>/resend/```

Resends the invitation to a pending jury member.

## Prize-pieces
Using ```GET /api/prizes/<prize_name>/pieces/```(paginated) jury members can see all submitted art works.
```
[{
    {
      "id": 10719,
      "title": "asdasd",
      "artist_name": jury ? <number_unique_by_artist_name> : <string>,
      "user_registered": jury ? <number_unique_by_artist_name> : <string>,
      "num_editions": -1,
      "datetime_registered": "2015-07-15T18:55:38.848148Z",
      "date_created": "2015-01-01",
      "thumbnail": {
        "id": 1866,
        "url": "https://d1qjsxua1o9x03.cloudfront.net/live/shit/8color/thumbnail/8color.jpg.png",
        "url_safe": "https://d1qjsxua1o9x03.cloudfront.net/live%2Fshit%2F8color%2Fthumbnail%2F8color.jpg.png",
        "mime": "image",
        "thumbnail_sizes": null
      },
      "license_type": {
        "name": "All rights reserved",
        "code": "default",
        "organization": "ascribe",
        "url": "https://www.ascribe.io/faq/#legals"
      },
      "bitcoin_id": "1E9HtDHduQf9XNnZ6ZgWwnxPCPcS2Lqb5v",
      "acl": {
        "acl_unconsign": false,
        "acl_edit": true,
        "acl_request_unconsign": false,
        "acl_view_editions": false,
        "acl_withdraw_transfer": false,
        "acl_view": true,
        "acl_coa": false,
        "acl_create_editions": false,
        "acl_download": true,
        "acl_unshare": false,
        "acl_share": true,
        "acl_delete": false,
        "acl_transfer": false,
        "acl_consign": false,
        "acl_loan": false,
        "acl_withdraw_consign": false
      },
      "extra_data": {},
      "digital_work": {
        "id": 2124,
        "url": "https://d1qjsxua1o9x03.cloudfront.net/live/shit/8color/digitalwork/8color.jpg",
        "url_safe": "https://d1qjsxua1o9x03.cloudfront.net/live%2Fshit%2F8color%2Fdigitalwork%2F8color.jpg",
        "mime": "image",
        "hash": "30a954018c7845629a6daf8ef58a9b89",
        "encoding_urls": null,
        "isEncoding": 0
      },
      "other_data": null,
      "prize": {
        "artist_statement": "This is a statement",
        "work_description": "This is an description",
        // jury ?
        "rating": {
            "personal": 1, // integer, can be null
            "overall": 4.5 // float, can be null
        }
      }
    }
}, ...]
```
Comment: A piece object does not contain information of an artist (`artist_name`, `user_registered` and so on).


Endpoint: ```POST /api/prizes/<prize_name>/pieces/```

Create and submit an new piece to the prize. The piece will appear as normal in the ascribe wallet.


Endpoint: ```POST /api/prizes/<prize_name>/pieces/<piece_id>/submit/```

Submit an existing piece to the prize, only for people who registered the piece.

## Prize-pieces ratings

Endpoint: ```GET /api/prizes/<prize_name>/pieces/<piece_id>/ratings/```

Payload:
```
{
    // this list can be of length zero
    "ratings": [
        {
            "user": "email@address.com",
            "rating": 4 // integer
        },
    ...],
    "personal": 4, // integer, can be null
    "overall": 4.5, // float, can be null
    "num_of_ratings": 2
}
```

Endpoint: ```POST /api/prizes/<prize_name>/pieces/<piece_id>/ratings/```

Payload:
```
{
    "rating": 4, // integer [0-5]
}
```