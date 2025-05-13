import requests

print(requests.get('http://127.0.0.1:5000/api/users').json())

print(requests.post('http://127.0.0.1:5000/api/users', json={
    'name': 'Name',
    'surname': 'Surname',
    'email': 'da@da.ca',
    'password': 'qwerty'
}).json())


print(requests.post('http://127.0.0.1:5000/api/users', json={
    'name': 'Name',
    'surname': 'Surname',
    'email': 'da@da.ca',
}).json())

print(requests.get('http://127.0.0.1:5000/api/users').json())