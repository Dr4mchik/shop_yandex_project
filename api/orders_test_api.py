import requests

print(requests.post('http://127.0.0.1:5000/api/orders/', json={'user_id': 3}).json())