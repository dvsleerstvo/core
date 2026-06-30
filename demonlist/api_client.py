import requests
from requests.exceptions import ChunkedEncodingError, RequestException

def fetch_api_level_list():
    try:
        response = requests.get('https://api.demonlist.org/level/classic/list',
                                timeout=10)
        return response.json().get('data', [])['levels']
    except Exception as e:
        print("Ошибка запроса к API:", e)
        return []

def get_player_id(username):
    try:
        print("Делаем запрос к https://api.demonlist.org/users/top...")
        url = 'https://api.demonlist.org/leaderboard/user/list'
        params = {
            'limit': 50,
            'offset': 0,
            'search': username.lower()
        }
        response = requests.get(url, params=params, timeout=300)
        response.raise_for_status()
        api_data = response.json().get('data', []).get('users', [])[0]
    except ChunkedEncodingError as e:
        print(f"ОШИБКА ChunkedEncodingError при запросе к /users/top: {e}")
        return {"status": "error", "message":
            f"Ошибка ChunkedEncodingError при получении топ-пользователей:"
            f" {e}"}
    except RequestException as e:
        print(f"ОШИБКА RequestException при запросе к /users/top: {e}")
        return {"status": "error", "message":
            f"Ошибка сети/соединения при получении топ-пользователей: {e}"}
    except Exception as e:
        print(f"НЕОЖИДАННАЯ ОШИБКА при запросе к /users/top: {e}")
        return {"status": "error", "message": e}

    return api_data

def get_player_records_from_api(demonlist_id):
    response_second = requests.get(
        f'http://api.demonlist.org/user/get?id={demonlist_id}'
        , timeout=60)

    response_second.raise_for_status()
    user_records = (response_second.json().get('data', {})
                    .get('levels', []))

    main = user_records.get('main', [])
    basic = user_records.get('extended', [])
    extended = user_records.get('advanced', [])
    beyond = user_records.get('unbounded', [])
    progress = user_records.get('progress', [])

    user_records = [*main, *basic, *extended, *beyond, *progress]
    return user_records

def get_level_info(placement):
    try:
        url = f'https://api.demonlist.org/level/classic/get?placement={placement}'
        level_data = requests.get(url)
    except Exception as e:
        print(e)
        return None
    return level_data