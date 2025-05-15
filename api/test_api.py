from requests import get, put, post

server = 'http://127.0.0.1:5000'

# пользователи

print(post(f'{server}/api/users', json={
    'email': 'evgeny_api@yandex.ru',
    'name': 'Evgeny',
    'surname': 'Zamury',
    'password': 'qwerty',
}).json())
print(post(f'{server}/api/users', json={
    'email': 'evgeny_api2@yandex.ru',
    'name': 'Evgeny2',
    'surname': 'Zamury2',
    'password': 'qwerty',
}).json())

print(put(f'{server}/api/users/2', json={
    'balance': 1000
}).json())

print(get(f'{server}/api/users').json())
print(get(f'{server}/api/users/1').json())
print()

# товары

print(post(f'{server}/api/products', json={
    'user_id': 1,
    'name': 'name_api',
    'price': '100',
    'open': 1,
    'amount_available': 100,
}).json())
print(get(f'{server}/api/products').json())
print(get(f'{server}/api/products/1').json())

print()
# заказы

print(post(f'{server}/api/orders_items', json={
    'user_id': 2,
    'product_id': 1,
    'amount': 1,
}).json())
print(get(f'{server}/api/orders_items').json())
print(get(f'{server}/api/orders_items/1').json())
print()

print(post(f'{server}/api/orders', json={
    'user_id': 2,
}).json())

print(put(f'{server}/api/orders/1', json={
    'status': 'delivered'
}).json())

print(get(f'{server}/api/orders').json())
print(get(f'{server}/api/orders/1').json())