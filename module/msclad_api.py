# module/msclad_api.py
import requests
from time import sleep
from typing import Optional, Dict, Any, List


def make_request(method: str, url: str, token: str, json_data: Optional[Dict] = None,
                 max_retries: int = 10, retry_delay: int = 10, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Универсальная функция для выполнения HTTP-запросов с повторными попытками

    Args:
        method: HTTP метод ('GET', 'POST', 'PUT')
        url: URL для запроса
        token: токен авторизации
        json_data: данные для отправки в JSON формате
        max_retries: максимальное количество попыток
        retry_delay: задержка между попытками в секундах
        timeout: таймаут запроса

    Returns:
        Ответ в формате JSON или None при ошибке
    """
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip"
    }

    for attempt in range(max_retries):
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=json_data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Обработка успешных статусов
            if response.status_code in [200, 412]:  # 412 - Precondition Failed, но может быть валидным ответом
                return response.json()
            elif response.status_code == 429:  # Too Many Requests
                print(f"Попытка {attempt + 1}: Превышен лимит запросов. Повтор через {retry_delay}сек")
                if attempt < max_retries - 1:
                    sleep(retry_delay)
            else:
                print(f"Ошибка {response.status_code}: {response.text}")
                return None

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"Попытка {attempt + 1} не удалась: {e}")
            if attempt < max_retries - 1:
                sleep(retry_delay)

    return None


def get_entities_paginated(token: str, entity_path: str,
                           params: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """
    Получение списка сущностей с поддержкой пагинации

    Args:
        token: токен авторизации
        entity_path: путь к сущности в API
        params: параметры запроса

    Returns:
        Список сущностей
    """
    base_url = f"https://api.moysklad.ru/api/remap/1.2/entity/{entity_path}"
    if params:
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        url = f"{base_url}?{query_string}"
    else:
        url = base_url

    entities = []
    current_url = url

    while current_url:
        response_data = make_request('GET', current_url, token)
        if not response_data:
            break

        entities.extend(response_data.get("rows", []))

        # Проверяем наличие следующей страницы
        meta = response_data.get('meta', {})
        current_url = meta.get('nextHref') if 'nextHref' in meta else None

    return entities


# Функции для работы с группами товаров
def get_productfolders(token: str, name: str = '') -> List[Dict[str, Any]]:
    """Получить список групп товаров"""
    params = {'filter': f'name={name}'} if name else None
    return get_entities_paginated(token, 'productfolder', params)


def post_productfolders(token: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Создать группу товаров"""
    return make_request('POST', 'https://api.moysklad.ru/api/remap/1.2/entity/productfolder',
                        token, json_data=data)


# Функции для работы с товарами/услугами
def get_items(token: str, item_type: str = 'product', name: str = '') -> List[Dict[str, Any]]:
    """Получить список товаров/услуг по имени"""
    params = {'search': name} if name else None
    return get_entities_paginated(token, item_type, params)


def get_items_filter(token: str, item_type: str = 'product',
                     filter_str: str = '') -> List[Dict[str, Any]]:
    """Получить список товаров/услуг по фильтру"""
    params = {'filter': filter_str} if filter_str else None
    return get_entities_paginated(token, item_type, params)


def get_item(token: str, item_id: str, item_type: str = 'product') -> Optional[Dict[str, Any]]:
    """Получить товар/услугу по ID"""
    url = f"https://api.moysklad.ru/api/remap/1.2/entity/{item_type}/{item_id}"
    return make_request('GET', url, token)


def post_item(token: str, data: Dict[str, Any], item_type: str) -> Optional[Dict[str, Any]]:
    """Создать сущность (товар/услугу/группу)"""
    url = f"https://api.moysklad.ru/api/remap/1.2/entity/{item_type}"
    return make_request('POST', url, token, json_data=data)


def put_item(token: str, url: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Изменить сущность"""
    return make_request('PUT', url, token, json_data=data)


# Функции для работы с метаданными
def get_meta_product(token: str) -> List[Dict[str, Any]]:
    """Получить метаданные атрибутов товаров"""
    return get_entities_paginated(token, 'product/metadata/attributes')


def get_meta_price(token: str) -> Optional[Dict[str, Any]]:
    """Получить метаданные типов цен"""
    url = 'https://api.moysklad.ru/api/remap/1.2/context/companysettings/pricetype'
    return make_request('GET', url, token)


# Функции для работы с документами
def get_document(token: str, url: str) -> Optional[Dict[str, Any]]:
    """Получить документ по URL"""
    return make_request('GET', url, token)


def post_document(token: str, url: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Создать документ"""
    return make_request('POST', url, token, json_data=data)


def put_document(token: str, url: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Изменить документ"""
    return make_request('PUT', url, token, json_data=data)


# Функции для работы с изображениями
def get_image(token: str, url: str) -> Optional[str]:
    """Получить URL изображения"""
    headers = {"Authorization": token, "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.url if response.status_code == 200 else None
    except requests.RequestException as e:
        print(f"Ошибка при загрузке изображения: {e}")
        return None


def post_image(token: str, image_data: Dict[str, Any], url: str) -> Optional[Dict[str, Any]]:
    """Добавить изображение"""
    return make_request('POST', url, token, json_data=image_data)


# Функции для работы с атрибутами
def get_attribute(token: str, code: str) -> List[Dict[str, Any]]:
    """Получить список атрибутов кастомной сущности"""
    return get_entities_paginated(token, f'customentity/{code}')


def post_prop_attribute(token: str, url: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Создать атрибут"""
    return make_request('POST', url, token, json_data=data)