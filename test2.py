

#!/usr/bin/python

import boto
import gcs_oauth2_boto_plugin
import os
import shutil
import StringIO
import tempfile
import time
from StringIO import StringIO
# URI scheme for Cloud Storage.
GOOGLE_STORAGE = 'gs'
# URI scheme for accessing local files.
LOCAL_FILE = 'file'






# Your project ID can be found at https://console.cloud.google.com/
# If there is no domain for your project, then project_id = 'YOUR_PROJECT'
project_id = 'mythic-producer-137123'
header_values = {"x-goog-project-id": project_id}

uri = boto.storage_uri('', GOOGLE_STORAGE)
# If the default project is defined, call get_all_buckets() without arguments.
for bucket in uri.get_all_buckets(headers=header_values):
  print bucket.name

#List each object from bucket
print 'listing content of a bucket'
uri = boto.storage_uri('pro-drive-cam-bucket', GOOGLE_STORAGE)
for obj in uri.get_bucket():
  print '%s://%s/%s' % (uri.scheme, uri.bucket_name, obj.name)
  # print '  "%s"' % obj.get_contents_as_string()




localfile='camera.jpg'


# Make some temporary files.
dst_uri = boto.storage_uri(
        'cloud-bucket' + '/' + localfile, GOOGLE_STORAGE)
# The key-related functions are a consequence of boto's
#interoperability with Amazon S3 (which employs the
# concept of a key mapping to localfile).
dst_uri.new_key().set_contents_from_file(StringIO(localfile))
print 'Successfully created "%s/%s"' % (
      dst_uri.bucket_name, dst_uri.object_name)

