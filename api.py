import os.path

import settings
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from datetime import datetime


class PetFriends:
    """
    API документация: https://petfriends.skillfactory.ru/apidocs/
    Класс содержит методы API
    """
    def __init__(self):
        self.base_url = 'https://petfriends.skillfactory.ru/'
        self.headers = {'Accept': 'application/json'}
        self.my_pets = []
        self.sess = requests.Session()
        try:
            if self.get_api_key():  # получаем api_key и сохраняем его в self.headers
                print(f'authorized with auth_key {self.headers["auth_key"]}')
                status_code, data = self.get_pets()
                if status_code == 200 and type(data) == list:
                    self.my_pets = data
                elif status_code == 200 and type(data) == dict:
                    self.my_pets.append(data)
                else:
                    print('error getting pets:', status_code, data)
            else:
                print(0, 'Unknown login error in __init__')
        except Exception as e:
            print(e)

    def request(self, method: str, path: str, headers: str = '', data = None, params = None) -> tuple:
        """
        Направляем запрос с регистрационными данными (если они существуют) возвращаем результат запроса
        Обязательные методы запроса 'GET', 'POST', 'PUT' or 'DELETE'
        Обязательный метод, добавляем путь к base_url для направляения запросов
        Опция настраиваемых headers (dict) или 'Content-Type' поля в headers (str).
        Опция тела запроса. Используем MultipartEncoder() если нужно использовать formData.
        Опция, дополнительные параметры к запросу - обычно GET's параметры добавляются в следующем виде: ?param1=value1&param2=value2&...
        возвращаем статус код ответа and response data
        """
        methods = ['GET', 'POST', 'PUT', 'DELETE']
        url = self.base_url + path if type(path) == str else ''
        if method.upper() not in methods:
            return (0, f'Unclear request method: {method}')
        if headers and type(headers) == dict:
            headers = self.headers | headers
        elif headers and type(headers) == str:
            headers = self.headers | {'Content-Type': headers}
        else:
            headers = self.headers
        if type(data) == MultipartEncoder:
            headers['Content-Type'] = data.content_type
        if not data:
            data = None
        if not params or type(params) != dict:
            params = None

        print(f'DEBUG: Request: {method} to {url}:\nparams={params}\nheaders={headers}\ndata={data}')

        resp = self.sess.request(method, url, params=params, data=data, headers=headers)
        if resp.headers['content-type'] == 'application/json':
            return resp.status_code, resp.json()
        else:
            return resp.status_code, resp.text

    def open_file(self, pet_photo: str):
        if not pet_photo:
            raise FileNotFoundError('Ошибка создания страницы моего питомца: не указана ссылка на фото')

        if '/' in pet_photo.replace('\\', '/'):
            file_name = pet_photo[pet_photo.replace('\\', '/').rindex('/')+1:]
        else:
            file_name = pet_photo
        ext = file_name[file_name.rindex('.') + 1:]
        if ext in ['jpg', 'jpeg']:
            photo_type = 'image/jpeg'
        elif ext == '.png':
            photo_type = 'image/x-png'
        elif ext == '.gif':
            photo_type = 'image/gif'
        else:
            raise FileNotFoundError('Файл не поддерживается:', pet_photo)

        try:
            f = open(pet_photo, 'rb')
        except FileNotFoundError:
            try:
                f = open(os.path.join(os.path.dirname(__file__), pet_photo), 'rb')
            except FileNotFoundError as e:
                raise FileNotFoundError('Ошибка создания страницы питомца: фото не найдено: ' + pet_photo)
        return file_name, f, photo_type

    @staticmethod
    def print_dict(data: dict) -> str:
        if type(data) == dict:
            for k in data.keys():
                if type(data[k]) == str and len(data[k]) > 127:
                    data[k] = data[k][:124] + '...'
                elif type(data[k]) == list:
                    data[k] = PetFriends.print_list(data[k])
        return str(data)

    @staticmethod
    def print_list(data: list) -> str:
        if type(data) == list:
            for i in range(len(data)):
                if type(data[i]) == dict:
                    data[i] = PetFriends.print_dict(data[i])
                elif type(data[i]) == str and len(data[i]) > 127:
                    data[i] = data[i][:124] + '...'
        return str(data)

    @staticmethod
    def print_resp(request_type: str, status_code: int, data: any) -> None:
        if status_code == 0:
            print(request_type, 'error:', data)
        else:
            if type(data) == dict:
                data = PetFriends.print_dict(data)
            elif type(data) == list:
                data = PetFriends.print_list(data)
            elif type(data) == str and len(data) > 127:
                data = data[:124] + '...'
        print(request_type, 'status code:', status_code)
        print(f'result = {data}')

    def get_api_key(self, force=False, email = None, password = None):
        """
        используем логин и пароль из импортируемого settings module для авторизации на сервере
        """
        if not force and 'auth_key' in self.headers: # Cached credinals
            return 200, self.headers['auth_key']
        if email == None:
            email = settings.valid_email
        if password == None:
            password = settings.valid_password
        try:
            headers = {'email': email, 'password': password}
            if not headers['email'] or not headers['password']:
                return 0, 'Поля с указанием электронной почты и пароля должны быть заполнены'
            if '@' not in headers['email'] or '.' not in headers['email'] or \
                headers['email'].index('@') > headers['email'].rindex('.') - 2:
                return 0, 'Неверный email'
        except ValueError as e:
            return 0, str(e)

        resp = self.request('GET', 'api/key', headers)
        if resp[0] == 200:
            if type(resp[1]) == dict and 'key' in resp[1].keys():
                self.headers['auth_key'] = resp[1]['key']
        return resp

    def get_pets(self, pet_id=None, auth_key=None, filter: str = 'my_pets') -> list:
        """
        возвращает список питомцев
        :param pet_id: информация о своих питомцах, либо инфа о всех питомцах
        :return: list object with found pets
        """
        if auth_key == None and 'auth_key' not in self.headers:
            return 0, 'Ошибка в получении списка питомцев: необходимо ввести ключ'
        headers = {}
        if type(auth_key) == str:
            headers['auth_key'] = auth_key
        if filter != 'my_pets':
            filter = ''
        resp = self.request('GET', 'api/pets', params={'filter': filter}, headers=headers)
        if resp[0] == 403 and auth_key == None:
            del self.headers['auth_key']
        else:
            if type(resp[1]) == dict and 'pets' in resp[1].keys() and type(resp[1]['pets']) == list:
                if filter == 'my_pets':
                    self.my_pets = resp[1]['pets']
                if pet_id:
                    pets = list(p for p in resp[1]['pets'] if type(p) == dict and 'id' in p.keys() and p['id'] == pet_id)
                    return pets
                else:
                    return resp[0], resp[1]['pets']
        return resp

    def create_pet(self, name: str, animal_type: str, age: int, pet_photo: str, bypass: bool = False) -> tuple:
        """
        создаем страницу питомца
        :param имя питомца, вид, возраст, фото
        :param bypass: Используется опционально, в целях тестирования.
        :return: возвращаем status code и данные о новом питомце
        """
        if bypass:
            pass
        elif 'auth_key' not in self.headers:
            return 0, 'Ошибка создания: пользователь не авторизован'
        elif not name:
            return 0, 'Ошибка создания: не введено имя питомца'
        elif type(age) == int and (age < 0 or age > 20) or type(age) == str and (int(age) < 0 or int(age) > 30):
            return 0, 'Ошибка создания: неправильный возраст'
        elif not animal_type:
            return 0, 'Ошибка создания: вид питомца не заполнен'

        try:
            pet_file = self.open_file(pet_photo)
        except FileNotFoundError:
            if bypass:
                pet_file = ''
            else:
                return 0, f'Ошибка создания: Фото {pet_photo} не найдено'
        data = MultipartEncoder(
            fields={
                'name': name if not bypass or name else '',
                'animal_type': animal_type if not bypass or animal_type else '',
                'age': str(age) if not bypass or age else '',
                'pet_photo': (pet_file[0], pet_file[1], pet_file[2]) if pet_file else ''
            }
        )
        resp = self.request('POST', 'api/pets', data=data)
        if resp[0] == 200:
            if type(resp[1]) == list:
                self.my_pets.append(resp[1])
                return resp[0], [p['id'] for p in resp[1]]

            if type(resp[1]) == dict:
                if 'id' in resp[1].keys() and 'created_at in resp[1].keys()':
                    self.my_pets.append(resp[1])
        elif resp[0] == 403:
            del self.headers['auth_key']
        return resp

    def update_pet(self, pet_id, name = None, animal_type = None, age = None, bypass: bool = False):
        """
        Изменение информации о питомце (имя, вид, возраст).
        :param pet_id питомца, информация о котором будет меняться, изменение в имени, виде, возрасте.
        :param bypass: опционально в целях тестирования.
        :return: возвращаем обновленную информацию о питомце
        """
        if 'auth_key' not in self.headers:
            return (0, 'Ошибка авторизации')
        if bypass:
            pass
        elif not self.my_pets or pet_id not in [p['id'] for p in self.my_pets]:
            return (0, 'Ошибка: питомец с указанным ID не найден. Pet_id = ' + str(pet_id))
        elif not name and not animal_type and not age:
            return (0, 'Ошибка: не введены параметры для обновления информации о питомце')
        try:
            pet_index = [p['id'] for p in self.my_pets].index(pet_id)
        except Exception:
            if not bypass:
                return 0, 'Ошибка. Питомец с данным ID не найден. pet_id = ' + str(pet_id)
        fields = {
            'name': name if name else (self.my_pets[pet_index]['name'] if not bypass else str(name)),
            'animal_type': animal_type if animal_type else (self.my_pets[pet_index]['animal_type'] if not bypass \
                                                            else str(animal_type)),
            'age': str(age) if age else (self.my_pets[pet_index]['age'] if not bypass else str(age))
        }
        data = MultipartEncoder(fields=fields)

        resp = self.request('PUT', 'api/pets/' + str(pet_id), data=data)

        if resp[0] == 200 and type(resp[1]) in [dict, list]:
            pet_index = [p['id'] for p in self.my_pets].index(pet_id)
            self.my_pets[pet_index] = resp[1]
            ex_text = 'Ошибка полученных данных:'
            if name and resp[1]['name'] != name:
                ex_text += f'\n - wrong name: \'{name}\' --> \'{resp[1]["name"]}\''
            if animal_type and resp[1]['animal_type'] != animal_type:
                ex_text += f'\n - wrong animal type: \'{animal_type}\' --> \'{resp[1]["animal_type"]}\''
            if age and resp[1]['age'] != str(age):
                ex_text += f'\n - wrong age: {age} --> {resp[1]["age"]}'
            if pet_id != resp[1]['id']:
                ex_text += f'\n - wrong ID: {pet_id} --> {resp[1]["id"]}'
            if len(ex_text) > 40:
                return (0, ex_text)
            return resp
        elif resp.status_code == 403:
            del self.headers['auth_key']
            return resp
        else:
            return (0, 'Update pet error' + str(resp[0]) + ': ' + str(resp[1]))

    def delete_pet(self, pet_id=None) -> None:
        """
        Удаление добавленного питомца
        :param pet_id питомца
        """
        # if type(self.my_pets) != list:
        #     self.my_pets = []
        if not pet_id and len(self.my_pets) > 0:
            # print(f'my_pets = ({type(self.my_pets)}) {self.my_pets}')
            pet_id = self.my_pets[0]['id']
        elif not pet_id:
            return (0, 'Ошибка удаления: не найден указанный id питомца')

        resp = self.request('DELETE', 'api/pets/' + str(pet_id))
        if resp[0] == 200:
           if pet_id in list(map(lambda p: p['id'], self.my_pets)):
                idx = list(i for i in range(len(self.my_pets)) if self.my_pets[i]['id'] == pet_id)
                for i in idx[::-1]:
                    self.my_pets.pop(i)
        return resp

    def create_pet_simple(self, name: str, animal_type: str, age: str, bypass: bool = False):
        """
        Создать питомца без добавления фото
        :param имя, вид, возраст
        :param Опционально в целях тестирования.
        :return: возвращает status_code и информацию
        """
        if not bypass and (not name or not animal_type or not age):
            return (0, f'values may not be empty:\n - name: {name}, animal_type: {animal_type}, age: {age}')
        data = MultipartEncoder(
            fields={
                'name': name,
                'animal_type': animal_type,
                'age': str(age)
            }
        )
        resp = self.request('POST', 'api/create_pet_simple', data=data)
        if resp[0] == 200 and type(resp[1]) == dict and 'id' in resp[1].keys():
            self.my_pets.append(resp[1])
        return resp

    def add_photo(self, pet_id: str, pet_photo: str, bypass: bool = False):
        """
        Замена/добавление фото
        :param pet_id, название файла с фото.
        :param bypass: Опционально в целях тестирования.
        :return: возвращаем статус и данные
        """
        try:
            f = self.open_file(pet_photo)
        except Exception as e:
            if not bypass:
                return 0, e
            data = MultipartEncoder(fields={'pet_photo': ''})
        else:
            data = MultipartEncoder(fields={'pet_photo': f})
        return self.request('POST', 'api/pets/set_photo/' + str(pet_id), data=data)

    def print_pets(self, pet=None) -> str:
        """
        Выводит информацию о питомцах в формате string
        :param указанные питомец/выборка питомцев, либо информация о всех питомцах
        """
        pets = ''
        if pet and type(pet) == list:
            for p in pet:
                if pets:
                    pets += '\n'
                pets = self.print_pets(p)
        elif pet and type(pet) == dict:
            pets = '{'
            for k in pet.items():
                if k[0] in ['id', 'age', 'animal_type', 'name']:
                    pets += '\n    \'' + k[0] + '\': \'' + k[1] + '\''
                elif k[0] == 'created_at':
                    pets += '\n    \'' + k[0] + '\': \'' + str(datetime.fromtimestamp(float(k[1]))) + '\''
                else:
                    pets += '\n    \'' + k[0] + '\': \'' + (k[1] if len(k[1]) < 128 else k[1][:125] + '...') + '\''
            pets += '\n}' if len(pets) > 3 else '}'
        elif len(self.my_pets) > 0:
            for p in self.my_pets:
                if pets:
                    pets += '\n'
                if p and type(p) == dict:
                    pets += '{'
                    for k in p.items():
                        if k[0] in ['id', 'age', 'animal_type', 'name']:
                            pets += '\n    \'' + k[0] + '\': \'' + k[1] + '\''
                        elif k[0] == 'created_at':
                            pets += '\n    \'' + k[0] + '\': \'' + str(datetime.fromtimestamp(float(k[1]))) + '\''
                        else:
                            pets += '\n    \'' + k[0] + '\': \'' + (k[1] if len(k[1]) < 128 else k[1][:125]+'...') + '\''
                    pets += '\n}'
        return pets
