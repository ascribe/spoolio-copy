import boto
AWS_ACCESS_KEY_ID = 'REDACTED'
AWS_SECRET_ACCESS_KEY = 'REDACTED'
AWS_STORAGE_BUCKET_NAME = 'ascribe0'

client = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
bucket = client.get_bucket(AWS_STORAGE_BUCKET_NAME)

multiparts = []
for key in bucket.get_all_multipart_uploads():
    try:
        assert key.to_xml() != '<CompleteMultipartUpload>\n</CompleteMultipartUpload>'
        print key.key_name
        multiparts.append(key)
        print 'added'
    except:
        print 'failed'
        pass

print multiparts