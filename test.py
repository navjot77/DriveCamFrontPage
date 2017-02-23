import urllib, urllib2, cookielib

#cookie_jar = cookielib.CookieJar()
#opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
#urllib2.install_opener(opener)

# acquire cookie
#url_1 = 'http://www.bkstr.com/webapp/wcs/stores/servlet/BuybackMaterialsView?langId=-1&catalogId=10001&storeId=10051&schoolStoreId=15828'
#req = urllib2.Request(url_1)
#rsp = urllib2.urlopen(req)




import requests

url='http://localhost:8080/getGPS'
username='t.chakal@yahoo.com'
password='avjot'

values = dict(x='37.376393',y='121.880617',vehicle='vehicle101')




r = requests.post(url, values,headers={'Authorization': '112233'})

print r.status_code
print r.headers['content-type']









# do POST
#url_2 = 'http://localhost:8080/getGPS'
#values = dict(x='37.376393',y='121.880617')
#data = urllib.urlencode(values)
#req = urllib2.Request(url_2, data)
#rsp = urllib2.urlopen(req)
#content = rsp.read()
#print content

# print result
#import re
#:w
#pat = re.compile('Title:.*')
#print pat.search(content).group()
