import requests
session = requests.Session()
res = session.get('http://localhost:8000/api/cart/')
csrftoken = session.cookies.get('csrftoken')
print(f"GET: {res.status_code}")
res2 = session.post('http://localhost:8000/api/cart/add/', json={'id': 'p1'}, headers={'X-CSRFToken': csrftoken})
print(f"POST add: {res2.status_code}, {res2.text[:50]}")
item_id = res2.json()['items'][0]['id']
res3 = session.patch(f'http://localhost:8000/api/cart/update/{item_id}/', json={'quantity': 2}, headers={'X-CSRFToken': csrftoken})
print(f"PATCH update: {res3.status_code}, {res3.text[:50]}")
res4 = session.delete(f'http://localhost:8000/api/cart/remove/{item_id}/', headers={'X-CSRFToken': csrftoken})
print(f"DELETE remove: {res4.status_code}, {res4.text[:50]}")
