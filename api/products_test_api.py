import requests

print(requests.get('http://127.0.0.1:5000/api/products').json())

print(requests.post('http://127.0.0.1:5000/api/products', json={
    'name': 'API топор',
    'price': 100,
    'open': 1,
}).json())


print(requests.post('http://127.0.0.1:5000/api/products', json={
    'name': 'API топор',
    'price': 'sad',
    'open': 1,
}).json())

print(requests.get('http://127.0.0.1:5000/api/products').json())