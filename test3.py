import request

request.post("https://www.googleapis.com/upload/storage/v1/b/myBucket/o?uploadType=media&name="+camera.jpg+",heaaders={'Content-Type': 'image/jpeg'})
