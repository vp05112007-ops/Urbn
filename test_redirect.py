import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import re

req = urllib.request.Request(
    'http://127.0.0.1:8000/accounts/google/login/', 
    data=b'', # POST request
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)

try:
    with urllib.request.urlopen(req) as response:
        print("Response:", response.status)
        print("URL:", response.geturl())
except urllib.error.HTTPError as e:
    print("Error:", e.code)
    print("Headers:", e.headers.get('Location'))
    location = e.headers.get('Location')
    if location:
        parsed = urllib.parse.urlparse(location)
        query = urllib.parse.parse_qs(parsed.query)
        print("client_id present:", 'client_id' in query)
        if 'client_id' in query:
            print("client_id length:", len(query['client_id'][0]))
