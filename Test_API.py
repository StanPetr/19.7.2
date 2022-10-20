import requests
import json

base_url = 'https://petstore.swagger.io/v2'

# GET /user/login  Logs user into the system

username = 'Ivan'  # Задаём имя пользователя
password = 123456  # Задаём пароль
user_data = {
  "id": 0,
  "username": "Ivan",
  "firstName": "Ivan",
  "lastName": "Ivanov",
  "email": "ivann@mail.org",
  "password": "123456",
  "phone": "+925225522",
  "userStatus": 0
}

res = requests.get(f'{base_url}/user/login?login={username}&password={password}',
                   headers={'accept': 'application/json'})

print('GET /user/login  Logs user into the system')
print('  Статус запроса:', res.status_code)
print('  Ответ сервера body:', res.json())
print('  Ответ сервера header:', res.headers, '\n')

# POST /user  Create user

body = json.dumps(user_data)

res = requests.post(f'{base_url}/user', headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                    data=body)

print('POST /user  Create user')
print('  Статус запроса:', res.status_code)
print('  Ответ сервера body:', res.json(), '\n')

# PUT /user/{username} Updated user

new_userdata = {
  "id": 0,
  "username": "Vanya",
  "firstName": "Vaniok",
  "lastName": "Ivanushkin",
  "email": "van@gog.org",
  "password": "asdfgh",
  "phone": "+9259966699",
  "userStatus": 0
}
body = json.dumps(new_userdata)

res = requests.put(f'{base_url}/user/{new_userdata}',
                   headers={'accept': 'application/json', 'Content-Type': 'application/json'}, data=body)

print(f'PUT /user/{new_userdata} Updated user')
print('  Статус запроса:', res.status_code)
print('  Ответ сервера body:', res.json(), '\n')

# GET /user/{username} Get user by user name (before delete)

username = new_userdata['username']

res = requests.get(f'{base_url}/user/{username}', headers={'accept': 'application/json'})

print('GET /user/{username} Get user by user name (before delete)')
print('  Статус запроса:', res.status_code)
print('  Ответ сервера body:', res.json(), '\n')

# DELETE /user/{username} Delete user

username = new_userdata['username']

res = requests.delete(f'{base_url}/user/{username}', headers={'accept': 'application/json'})

print('DELETE /user/{username} Delete user')
print('  Статус запроса:', res.status_code)
print('  Ответ сервера body:', res.json(), '\n')
