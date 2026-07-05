class Player:
    def __init__(self, chat_id, user_id, name, photo, exp=0, money=100, hp=100, damage=20, luck=0.2, level=1):
        self.chat_id = chat_id
        self.user_id = user_id
        self.name = name
        self.photo = photo
        self.exp = exp
        self.money = money
        self.hp = hp
        self.damage = damage
        self.luck = luck
        self.level = level

    def __str__(self):
        return f"{self.name} (Ур. {self.level})"
    
    def get_exp_for_next_level(self):
        """Расчет опыта для перехода на следующий уровень"""
        # Формула: 50 * level + 50 * (level^2) / 2
        # Для 30 уровней: примерно 50->150->300->500->...
        return int(50 * self.level + 50 * (self.level ** 2) / 2)
    
    def get_max_level(self):
        return 30
    
    def add_exp(self, amount):
        """Добавить опыт и повысить уровень при необходимости"""
        self.exp += amount
        
        # Повышаем уровни пока есть достаточно опыта
        leveled_up = False
        while self.level < self.get_max_level():
            needed = self.get_exp_for_next_level()
            if self.exp >= needed:
                self.exp -= needed
                self.level += 1
                self.apply_level_bonus()
                leveled_up = True
            else:
                break
        
        # Если достигнут максимальный уровень
        if self.level >= self.get_max_level():
            self.exp = 0  # На макс уровне опыт не нужен
        
        return leveled_up
    
    def apply_level_bonus(self):
        """Применить бонусы за новый уровень"""
        # За каждый уровень: +2 к урону, +5% удачи (но не более 80%)
        self.damage += 2
        self.luck = min(0.8, self.luck + 0.05)


class Achievement:
    def __init__(self, id, name, photo, condition, description):
        self.id = id
        self.name = name
        self.image = photo
        self.condition = condition
        self.description = description


class Task:
    def __init__(self, id, name, chat_id, owner_id, money, duration, worker_id=None):
        self.id = id
        self.name = name
        self.chat_id = chat_id
        self.owner_id = owner_id
        self.money = money
        self.duration = duration
        self.worker_id = worker_id


class Event:
    def __init__(self, id, name, datetime, chat_id, user_id):
        self.id = id
        self.name = name
        self.datetime = datetime
        self.chat_id = chat_id
        self.user_id = user_id


class Boss:
    def __init__(self, id, name, photo, hp, damage, luck, money_reward, exp_reward):
        self.id = id
        self.name = name
        self.photo = photo
        self.hp = hp
        self.damage = damage
        self.luck = luck
        self.money_reward = money_reward
        self.exp_reward = exp_reward


class Item:
    def __init__(self, id, name, price, description, type):
        self.id = id
        self.name = name
        self.price = price
        self.description = description
        self.type = type