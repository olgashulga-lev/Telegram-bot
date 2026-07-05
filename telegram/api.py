import requests
import configparser
from pathlib import Path
from models import Player, Achievement, Task, Event, Boss, Item

config = configparser.ConfigParser()
config.read('config.ini')
BACKEND_URL = f"http://{config['DEFAULT']['BACKHOST']}:{config['DEFAULT']['BACKPORT']}/api"

def _make_request(method, endpoint, data=None, params=None):
    url = f"{BACKEND_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, params=params)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, params=params)
        elif method == "DELETE":
            response = requests.delete(url, json=data, headers=headers, params=params)
        else:
            return None
        
        if response.status_code >= 400:
            print(f"Ошибка {response.status_code}: {response.text}")
            return None
        return response.json()
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None

#Игроки 

def get_player(chat_id, user_id):
    data = _make_request("GET", f"person/id/{chat_id}")
    if not data:
        return None
    
    for player_data in data:
        if player_data.get('userId') == user_id or player_data.get('user_id') == user_id:
            return Player(
                chat_id=chat_id,
                user_id=user_id,
                name=player_data.get('name', 'Unknown'),
                photo=player_data.get('photo', 'default.jpg'),
                exp=player_data.get('experience', 0),
                money=player_data.get('money', 100),
                hp=player_data.get('hp', 100),
                damage=player_data.get('damage', 20),
                luck=player_data.get('luck', 20) / 100,
                level=player_data.get('level', 1)
            )
    return None

def create_player(player):
    data = {
        'user_id': player.user_id,
        'chat_id': player.chat_id,
        'name': player.name,
        'photo': player.photo,
        'experience': player.exp,
        'money': player.money,
        'hp': player.hp,
        'damage': player.damage,
        'luck': int(player.luck * 100),
        'level': player.level
    }
    return _make_request("POST", "person/create_alt", data)

def update_player(player):
    data = {
        'name': player.name,
        'experience': player.exp,
        'money': player.money,
        'hp': player.hp,
        'damage': player.damage,
        'luck': int(player.luck * 100),
        'level': player.level
    }
    params = {'chat_id': player.chat_id, 'user_id': player.user_id}
    return _make_request("PUT", "person/update", data, params)

def get_all_players(chat_id):
    # Вместо фильтрации по чату - получаем ВСЕХ игроков
    data = _make_request("GET", "person/all")  # Новый эндпоинт
    if not data:
        return []
    
    players = []
    for p in data:
        players.append(Player(
            chat_id=p.get('chatId', chat_id),
            user_id=p['userId'],
            name=p['name'],
            photo=p['photo'],
            exp=p.get('experience', 0),
            money=p.get('money', 100),
            hp=p.get('hp', 100),
            damage=p.get('damage', 20),
            luck=p.get('luck', 20) / 100,
            level=p.get('level', 1)
        ))
    return players

def get_all_players_global():
    """Получить всех игроков из всех чатов"""
    data = _make_request("GET", "person/all")
    if not data:
        return []
    
    players = []
    for p in data:
        players.append(Player(
            chat_id=p.get('chatId', 0),
            user_id=p['userId'],
            name=p['name'],
            photo=p['photo'],
            exp=p.get('experience', 0),
            money=p.get('money', 100),
            hp=p.get('hp', 100),
            damage=p.get('damage', 20),
            luck=p.get('luck', 20) / 100,
            level=p.get('level', 1)
        ))
    return players

def get_and_update_player_with_exp(chat_id, user_id, exp_gain):
    """Получить игрока, добавить опыт и вернуть обновленного"""
    player = get_player(chat_id, user_id)
    if not player:
        return None, False
    
    # Добавляем опыт
    leveled_up = player.add_exp(exp_gain)
    
    # Обновляем в БД
    update_player(player)
    
    return player, leveled_up

def get_player_exp_for_level(level):
    """Получить опыт для указанного уровня"""
    # Используем ту же формулу что и в Player
    return int(50 * level + 50 * (level ** 2) / 2)

def get_max_level():
    return 30

#Достижения 

def get_user_achievements(chat_id, user_id):
    data = _make_request("GET", f"achievement/person/{chat_id}/{user_id}")
    if not data:
        return []
    
    achievements = []
    for a in data:
        achievements.append(Achievement(
            id=a['id'],
            name=a['name'],
            photo=a['photo'],
            condition=a['condition'],
            description=a['description']
        ))
    return achievements

def give_achievement(chat_id, user_id, name, description, condition=None):
    """Выдать достижение игроку"""
    data = {
        'user_id': user_id,
        'chat_id': chat_id,
        'name': name,
        'description': description,
        'condition': condition or '',
        'image': 'default_achievement.jpg'
    }
    return _make_request("POST", "achievement/create", data)

#Задания

def get_free_tasks(chat_id):
    data = _make_request("GET", "task/free")
    if not data:
        return []
    
    tasks = []
    for t in data:
        # Исправление: проверяем, что задание принадлежит этому чату и не имеет исполнителя
        if t.get('chatId') == chat_id and t.get('workerUserId') is None:
            tasks.append(Task(
                id=t['id'],
                name=t['name'],
                chat_id=t['chatId'],
                owner_id=t['ownerUserId'],
                money=t['money'],
                duration=t['duration']
            ))
    return tasks

def create_task(chat_id, owner_id, name, money, duration):
    """Создать задание"""
    data = {
        'name': name,
        'money': money,
        'duration': duration,
        'chat_id': chat_id,  # меняем на chat_id
        'owner_user_id': owner_id  # меняем на owner_user_id
    }
    print(f"📤 Создание задания: {data}")
    result = _make_request("POST", "task/create", data)
    print(f"📥 Результат: {result}")
    return result is not None

def take_task(task, worker_id):
    data = {
        'id': task.id,
        'workerUserId': worker_id
    }
    return _make_request("PUT", "task/update", data)

def complete_task(task):
    return _make_request("DELETE", f"task/delete/{task.id}")

#Мероприятия

def create_event(chat_id, user_id, name, datetime):
    """Создать мероприятие"""
    data = {
        'name': name,
        'datetime': datetime,
        'chat_id': chat_id,
        'user_id': user_id
    }
    print(f"📤 Создание мероприятия: {data}")
    result = _make_request("POST", "event/create", data)
    print(f"📥 Результат: {result}")
    return result is not None

def get_events(chat_id):
    data = _make_request("GET", f"event/chat/{chat_id}")
    if not data:
        return []
    
    events = []
    for e in data:
        events.append(Event(
            id=e['id'],
            name=e['name'],
            datetime=e.get('startedAt', 'Неизвестно'),  # Исправлено: startedAt вместо datetime
            chat_id=e.get('chatId', chat_id),
            user_id=e.get('userId', 0)
        ))
    return events

#Боссы

def get_bosses():
    return [
        Boss(1, "Батя Коллектора", "father.jpg", 500, 40, 0.3, 500, 400),
        Boss(2, "Кыксик", "kiksik.jpg", 450, 35, 0.5, 600, 500),
        Boss(3, "Жаба", "frog.jpg", 700, 25, 0.1, 800, 600),
    ]

#Предметы

def get_items():
    data = _make_request("GET", "item/all")
    if not data:
        return []
    
    items = []
    for i in data:
        items.append(Item(
            id=i['id'],
            name=i['name'],
            price=i['price'],
            description=i['description'],
            type=i['type']
        ))
    return items

def add_item_to_inventory(chat_id, user_id, item_id, item_name, item_type, quantity=1):
    data = {
        'user_id': user_id,
        'chat_id': chat_id,
        'item_id': item_id,
        'item_name': item_name,
        'item_type': item_type,
        'quantity': quantity
    }
    return _make_request("POST", "inventory/add", data=data)

def get_inventory(chat_id, user_id):
    data = _make_request("GET", f"inventory/{chat_id}/{user_id}")
    if not data:
        return []
    
    items = []
    for i in data:
        items.append({
            'id': i.get('id'),
            'item_id': i.get('item_id'),
            'name': i.get('name'),
            'type': i.get('type'),
            'quantity': i.get('quantity', 1)
        })
    return items

#Зелья
def get_active_effects(chat_id, user_id):
    """Получить активные эффекты игрока"""
    data = _make_request("GET", f"effects/{chat_id}/{user_id}")
    if not data:
        return []
    return data

def apply_effect(chat_id, user_id, effect_type, value, duration_seconds):
    """Применить эффект к игроку"""
    params = {
        'chat_id': chat_id,
        'user_id': user_id,
        'effect_type': effect_type,
        'value': value,
        'duration_seconds': duration_seconds
    }
    return _make_request("POST", "effects/apply", data=None, params=params)

def clear_expired_effects(chat_id, user_id):
    """Очистить истекшие эффекты"""
    return _make_request("DELETE", f"effects/clear/{chat_id}/{user_id}")

def use_item_in_battle(chat_id, user_id, item_id):
    """Использовать предмет в бою (для зелий здоровья)"""
    # Проверяем инвентарь
    inventory = get_inventory(chat_id, user_id)
    item = next((i for i in inventory if i.get('item_id') == item_id), None)
    
    if not item or item.get('quantity', 0) <= 0:
        return None
    
    # Для зелья здоровья - восстанавливаем HP
    if item_id == 1:  # Зелье здоровья
        player = get_player(chat_id, user_id)
        if player:
            heal_amount = 20
            player.hp = min(100, player.hp + heal_amount)
            update_player(player)
            # Удаляем одно зелье из инвентаря
            item['quantity'] -= 1
            if item['quantity'] <= 0:
                # Удаляем из инвентаря
                _make_request("DELETE", f"inventory/remove/{item['id']}")
            else:
                # Обновляем количество
                _make_request("PUT", "inventory/update", data={
                    'inventory_id': item['id'],
                    'quantity': item['quantity']
                })
            return {'healed': heal_amount, 'new_hp': player.hp}
    
    return None