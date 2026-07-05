import requests
from models import Player, Achievement, Task, Event, Boss, Item

BACKEND_URL = "http://localhost:8000/api"

def _make_request(method, endpoint, data=None, params=None):
    url = f"{BACKEND_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
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

# Игроки
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
                luck=player_data.get('luck', 0.2),
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
        'luck': int(player.luck * 100)
    }
    return _make_request("POST", "person/create_alt", data)

def update_player(player):
    data = {
        'name': player.name,
        'experience': player.exp,
        'money': player.money,
        'hp': player.hp,
        'damage': player.damage,
        'luck': int(player.luck * 100)
    }
    params = {'chat_id': player.chat_id, 'user_id': player.user_id}
    return _make_request("PUT", "person/update", data, params)

def get_all_players(chat_id):
    data = _make_request("GET", f"person/id/{chat_id}")
    if not data:
        return []
    
    players = []
    for p in data:
        players.append(Player(
            chat_id=chat_id,
            user_id=p['userId'],
            name=p['name'],
            photo=p['photo'],
            exp=p.get('experience', 0),
            money=p.get('money', 100),
            hp=p.get('hp', 100),
            damage=p.get('damage', 20),
            luck=p.get('luck', 0.2),
            level=p.get('level', 1)
        ))
    return players

# Достижения
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

# Задания
def get_free_tasks(chat_id):
    data = _make_request("GET", "task/free")
    if not data:
        return []
    
    tasks = []
    for t in data:
        if t['chatId'] == chat_id and t['workerUserId'] is None:
            tasks.append(Task(
                id=t['id'],
                name=t['name'],
                chat_id=t['chatId'],
                owner_id=t['ownerUserId'],
                money=t['money'],
                duration=t['duration']
            ))
    return tasks

def take_task(task, worker_id):
    data = {
        'id': task.id,
        'worker_user_id': worker_id
    }
    return _make_request("PUT", "task/update", data)

def complete_task(task):
    return _make_request("DELETE", f"task/delete/{task.id}")

# Мероприятия
def get_events(chat_id):
    data = _make_request("GET", f"event/chat/{chat_id}")
    if not data:
        return []
    
    events = []
    for e in data:
        events.append(Event(
            id=e['id'],
            name=e['name'],
            datetime=e['startedAt'],
            chat_id=e.get('chatId', chat_id),
            user_id=e.get('userId', 0)
        ))
    return events

# Боссы
def get_bosses():
    return [
        Boss(1, "Батя Коллектора", "father.jpg", 500, 40, 0.3, 500, 400),
        Boss(2, "Кыксик", "kiksik.jpg", 450, 35, 0.5, 600, 500),
        Boss(3, "Жаба", "frog.jpg", 700, 25, 0.1, 800, 600),
    ]

# Предметы
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