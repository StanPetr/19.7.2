import settings
from api import PetFriends
from settings import valid_email, valid_password, invalid_email, invalid_password
from requests_toolbelt import MultipartEncoder
import os
import pytest

pf = PetFriends()

def test_get_api_key_for_invalid_user(email=settings.invalid_email, password=settings.invalid_password):
    """
    Негативный тест на ввод неверных данных
    """
    status, result = pf.get_api_key(force=True, email=email, password=password)

    assert status == 403

def test_get_api_key_valid_user(email=valid_email, password=valid_password):
    """
    Получаем ключ auth_key для верных данных (email, password)
    """
    status, result = pf.get_api_key()

    assert status == 200
    assert type(result) is str and len(result) > 0

def test_get_all_pets_valid_key(filter=''):
    """ Проверяем что запрос всех питомцев возвращает не пустой список.
    Получаем api ключ и сохраняем в переменную auth_key. Далее используя ключ
    запрашиваем список всех питомцев и проверяем что список не пустой.
    Доступное значение параметра filter - 'my_pets' либо '' """

    if 'auth_key' not in pf.headers:
        pf.get_api_key()

    status_code, list_pets = pf.get_pets(filter=filter)

    assert status_code == 200 and type(list_pets) == list
    assert len(list_pets) >= 0
    if len(list_pets) > 0:
        assert type(list_pets[0]) == dict
        assert 'id' in list_pets[0].keys()

def test_get_pets_invalid_key(api_key = 'none'):
    """
    негативный тест с неправильной авторизацией
    """
    status_code, list_pet = pf.get_pets(auth_key=api_key)
    assert status_code == 403

def test_get_my_pets():
    status, resp = pf.get_pets(filter='')
    assert status == 200 and type(resp) == list

def test_add_new_pet_valid_data(name='жакки', animal_type='пес', age=6, pet_photo='photo/dog1.jpg'):
    """Проверяем что можно добавить питомца с корректными данными"""
    pet_photo = os.path.join(os.path.dirname(__file__), pet_photo)
    status, new_pet = pf.create_pet(name, animal_type, age, pet_photo)

    assert status == 200
    assert type(new_pet) == dict
    assert 'name' in new_pet.keys() and new_pet['name'] == name

def test_add_new_pet_partial_data(name='', animal_type='кот', age=-1, pet_photo='', bypass=True):
    """Проверяем что можно добавить питомца с корректными данными"""
    status, new_pet = pf.create_pet(name, animal_type, age, pet_photo, bypass=bypass)
    assert status == 400

def test_add_new_pet_invalid_data(name='\n', animal_type='\t', age='55', pet_photo='', bypass=True):
    """Проверяем что можно добавить питомца с корректными данными"""
    status, new_pet = pf.create_pet(name, animal_type, age, pet_photo, bypass=True)
    assert status == 400

def test_create_pet_simple_correct(name='Персик', animal_type='дворянский', age=1):
    status, resp = pf.create_pet_simple(name, animal_type, age)
    assert status == 200
    assert type(resp) in [list, dict]

def test_create_pet_simple_invalid(method='POST', path='api/create_pet_simple', body={'name': '', 'age':'3'}):
    """
    Проверяем неправильный запрос на создание питомца
    """
    data = MultipartEncoder(fields=body)
    status, _ = pf.request(method, path, data.content_type, data)

    assert status == 400

def test_update_pet(name='Тушенка', animal_type='кошка', age=5):
    """Проверяем возможность обновления информации о питомце"""
    _, my_pets = pf.get_pets()

    if len(my_pets) == 0:
        _, pet = pf.create_pet("Сгущенка", "кошечка", "2", "photo/cat1.jpg")
        my_pets = [pet]

    status, result = pf.update_pet(my_pets[0]['id'], name, animal_type, age)

    assert status == 200
    assert result['name'] == name
    assert result['animal_type'] == animal_type
    assert result['age'] == str(age)

def test_add_invalid_photo(pet_photo=''):
    """Проверяем запрос на добавление фото с пустым фото"""

    my_pets = pf.get_pets()
    pet_id = None
    if type(my_pets) == list and len(my_pets) > 0:
        for i in range(len(pf.my_pets)):
            if type(my_pets[i]) == dict and 'id' in my_pets[i].keys() and 'pet_photo' in my_pets[i].keys() \
                and my_pets[i]['pet_photo'] == '':
                pet_id = i
                break

    if pet_id == None:
        _, pets = pf.create_pet_simple('Мурзик', 'котей', '10')
        pet_id = pets['id']

    status, resp = pf.add_photo(pet_id, pet_photo, bypass=True)
    assert status == 400

def test_add_valid_photo(pet_photo='photo/cat1.jpg'):

    my_pets = pf.get_pets()

    pet_id = None
    if type(my_pets) == list and len(my_pets) > 0:
        for i in range(len(pf.my_pets)):
            if type(my_pets[i]) == dict and 'id' in my_pets[i].keys() and 'pet_photo' in my_pets[i].keys() \
                and my_pets[i]['pet_photo'] == '':
                pet_id = i
                break

    if pet_id == None:
        _, pets = pf.create_pet_simple('Мурзик', 'котей', '10')
        pet_id = pets['id']

    status, resp = pf.add_photo(pet_id, pet_photo)

    assert status == 200
    assert resp['pet_photo'][:23] == 'data:image/jpeg;base64,'

def test_delete_self_pet():
    """Проверяем возможность удаления питомца"""
    _, my_pets = pf.get_pets()

    if len(my_pets) == 0:
        _, pet = pf.create_pet("Сгущенка", "кошечка", "2", "photo/cat1.jpg")
        my_pets = [pet]

    pet_id = my_pets[0]['id']

    _, my_pets = pf.get_pets()

    pet_ids = [p['id'] for p in my_pets]     # Проверяем что в списке питомцев нет id удалённого питомца
    assert pet_id is not None
    assert pet_id not in my_pets

def test_delete_pet_incorrect_id(pet_id = '99999999999'):
    """Проверяем возможность удаления питомца"""

    _, my_pets = pf.get_pets() # запрашиваем список своих питомцев

    if len(my_pets) > 0:  # если есть питомцы, проверяем, что питомца нет среди моих питомцев:
        assert pet_id not in list(map(lambda x: x['id'], my_pets))

    status, resp = pf.delete_pet(pet_id) # удаляем питомца с неправильным ключом

    assert status == 200