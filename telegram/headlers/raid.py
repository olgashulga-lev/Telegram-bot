from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import api
from .common_utils import get_player_or_none
import random
import asyncio
import uuid

router = Router()
active_raids = {}

def generate_raid_id():
    return str(uuid.uuid4())[:8]

async def perform_raid_battle(raid, boss, callback=None):
    total_damage = 0
    boss_hp = raid.get('boss_current_hp', boss.hp)
    players_names = []
    players_damage = []
    players_data = []
    
    for user_id in raid['players']:
        player = None
        for p in api.get_all_players():
            if p.user_id == user_id:
                player = p
                break
        if player:
            api.clear_expired_effects(player.chat_id, user_id)
    
    for user_id in raid['players']:
        player = None
        player_chat_id = None
        
        all_players = api.get_all_players()
        for p in all_players:
            if p.user_id == user_id:
                player = p
                player_chat_id = p.chat_id
                break
        
        if player:
            players_names.append(player.name)
            players_data.append(player)
            
            effects = api.get_active_effects(player_chat_id, user_id) if player_chat_id else []
            
            base_damage = player.damage
            damage_bonus = 0
            for e in effects:
                if e.get('effect_type') == 'damage_bonus':
                    damage_bonus += e.get('value', 0)
            
            total_player_damage = base_damage + damage_bonus
            damage = random.randint(5, 20) + total_player_damage // 5
            
            total_damage += damage
            boss_hp -= damage
            players_damage.append(damage)
    
    return {
        'total_damage': total_damage,
        'boss_hp': boss_hp,
        'players_names': players_names,
        'players_damage': players_damage,
        'players_data': players_data
    }

@router.message(Command("raid"))
async def cmd_raid(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    if not active_raids:
        await message.answer(
            "Активных рейдов нет!\n\n"
            "Создайте свой рейд командой:\n"
            "/boss1 - Батя Коллектора\n"
            "/boss2 - Кыксик\n"
            "/boss3 - Жаба"
        )
        return
    
    text = "<b>АКТИВНЫЕ РЕЙДЫ:</b>\n\n"
    
    for raid_id, raid in active_raids.items():
        boss = next((b for b in api.get_bosses() if b.id == raid['boss_id']), None)
        if boss:
            creator = None
            all_players = api.get_all_players()
            for p in all_players:
                if p.user_id == raid['creator_id']:
                    creator = p
                    break
            
            creator_name = creator.name if creator else f"Игрок {raid['creator_id']}"
            
            is_participant = message.from_user.id in raid['players']
            status = "ВЫ УЧАСТВУЕТЕ" if is_participant else f"{len(raid['players'])}/5"
            
            text += f"<b>{boss.name}</b>\n"
            text += f"Создатель: {creator_name}\n"
            text += f"{status}\n"
            text += f"HP: {raid.get('boss_current_hp', boss.hp)}\n"
            
            if not is_participant and raid['status'] == 'recruiting':
                text += f"/join {creator_name} - присоединиться\n"
            elif is_participant:
                text += f"Вы уже в этом рейде!\n"
            else:
                text += f"Рейд уже начался!\n"
            
            text += "\n"
    
    await message.answer(text)

@router.message(Command("join"))
async def cmd_join_by_name(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "Укажите имя создателя рейда:\n"
            "/join ИгрокА\n\n"
            "Список активных рейдов: /raid"
        )
        return
    
    creator_name = ' '.join(args[1:]).strip()
    
    found_raid = None
    found_raid_id = None
    
    for raid_id, raid in active_raids.items():
        if raid['status'] != 'recruiting':
            continue
            
        creator = None
        all_players = api.get_all_players()
        for p in all_players:
            if p.user_id == raid['creator_id']:
                creator = p
                break
        
        if creator and creator.name.lower() == creator_name.lower():
            found_raid = raid
            found_raid_id = raid_id
            break
    
    if not found_raid:
        await message.answer(
            f"Рейд с создателем '{creator_name}' не найден!\n"
            f"Используйте /raid для списка активных рейдов."
        )
        return
    
    for other_raid in active_raids.values():
        if message.from_user.id in other_raid['players']:
            await message.answer("Вы уже участвуете в другом рейде!")
            return
    
    if len(found_raid['players']) >= found_raid.get('max_players', 5):
        await message.answer("Рейд полон! (максимум 5 игроков)")
        return
    
    found_raid['players'].append(message.from_user.id)
    
    creator = None
    all_players = api.get_all_players()
    for p in all_players:
        if p.user_id == found_raid['creator_id']:
            creator = p
            break
    
    if creator:
        try:
            await message.bot.send_message(
                chat_id=creator.chat_id,
                text=f"Игрок {player.name} присоединился к вашему рейду!\n"
                     f"Теперь участников: {len(found_raid['players'])}\n\n"
                     f"Когда наберётся 2+ игроков, нажмите «Начать бой»"
            )
        except:
            pass
    
    await message.answer(
        f"Вы присоединились к рейду {creator_name}!\n"
        f"Участников: {len(found_raid['players'])}\n\n"
        f"Команды:\n"
        f"/raid_status - статус рейда\n"
        f"/leave_raid - выйти из рейда"
    )

async def start_raid(message: types.Message, boss_id: int):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    bosses = api.get_bosses()
    boss = next((b for b in bosses if b.id == boss_id), None)
    if not boss:
        await message.answer("Такого босса нет!")
        return
    
    for raid in active_raids.values():
        if message.from_user.id in raid['players']:
            await message.answer("Вы уже участвуете в другом рейде!")
            return
    
    raid_id = generate_raid_id()
    
    active_raids[raid_id] = {
        'boss_id': boss_id,
        'players': [message.from_user.id],
        'status': 'recruiting',
        'boss_current_hp': boss.hp,
        'creator_id': message.from_user.id,
        'max_players': 5,
        'created_at': message.date,
        'creator_name': player.name
    }
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Начать бой",
                    callback_data=f"start_raid_battle_{raid_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отменить рейд",
                    callback_data=f"cancel_raid_{raid_id}"
                )
            ]
        ]
    )
    
    await message.answer(
        f"<b>Рейд создан!</b>\n\n"
        f"Босс: {boss.name}\n"
        f"HP: {boss.hp}\n"
        f"Награда: {boss.money_reward} монет\n"
        f"Опыт: {boss.exp_reward}\n\n"
        f"Создатель: {player.name}\n"
        f"Участников: 1/5\n\n"
        f"Друзья могут присоединиться из любого чата с ботом:\n"
        f"/join {player.name}\n\n"
        f"Когда наберётся 2+ игроков, нажмите «Начать бой»",
        reply_markup=keyboard
    )

@router.message(Command("boss1"))
async def cmd_boss1(message: types.Message):
    await start_raid(message, 1)

@router.message(Command("boss2"))
async def cmd_boss2(message: types.Message):
    await start_raid(message, 2)

@router.message(Command("boss3"))
async def cmd_boss3(message: types.Message):
    await start_raid(message, 3)

@router.message(Command("raid_status"))
async def cmd_raid_status(message: types.Message):
    raid_data = None
    raid_id = None
    
    for r_id, raid in active_raids.items():
        if message.from_user.id in raid['players']:
            raid_data = raid
            raid_id = r_id
            break
    
    if not raid_data:
        await message.answer("Вы не участвуете ни в одном рейде!")
        return
    
    boss = next((b for b in api.get_bosses() if b.id == raid_data['boss_id']), None)
    if not boss:
        await message.answer("Ошибка!")
        return
    
    players_names = []
    all_players = api.get_all_players()
    for user_id in raid_data['players']:
        for p in all_players:
            if p.user_id == user_id:
                players_names.append(p.name)
                break
    
    text = f"<b>СТАТУС РЕЙДА</b>\n\n"
    text += f"Босс: {boss.name}\n"
    text += f"HP босса: {raid_data.get('boss_current_hp', boss.hp)}/{boss.hp}\n"
    text += f"Участников: {len(raid_data['players'])}/5\n"
    text += f"Статус: {'Набор' if raid_data['status'] == 'recruiting' else 'Битва'}\n\n"
    
    if players_names:
        text += "<b>Участники:</b>\n"
        for i, name in enumerate(players_names, 1):
            text += f"{i}. {name}\n"
    
    await message.answer(text)

@router.message(Command("leave_raid"))
async def cmd_leave_raid(message: types.Message):
    for raid_id, raid in active_raids.items():
        if message.from_user.id in raid['players']:
            if raid['status'] != 'recruiting':
                await message.answer("Нельзя выйти из рейда во время битвы!")
                return
            
            raid['players'].remove(message.from_user.id)
            
            creator = None
            all_players = api.get_all_players()
            for p in all_players:
                if p.user_id == raid['creator_id']:
                    creator = p
                    break
            
            if creator:
                try:
                    await message.bot.send_message(
                        chat_id=creator.chat_id,
                        text=f"Игрок покинул рейд!\n Осталось: {len(raid['players'])}"
                    )
                except:
                    pass
            
            if len(raid['players']) == 0:
                del active_raids[raid_id]
                await message.answer("Рейд удалён (не осталось участников)")
                return
            
            await message.answer(f"Вы покинули рейд!\n Осталось: {len(raid['players'])}")
            return
    
    await message.answer("Вы не участвуете ни в одном рейде!")

@router.callback_query(F.data.startswith("start_raid_battle_"))
async def cmd_raid_battle(callback: types.CallbackQuery):
    raid_id = callback.data.replace("start_raid_battle_", "")
    
    if raid_id not in active_raids:
        await callback.answer("Рейд уже завершён!")
        return
    
    raid = active_raids[raid_id]
    
    if raid['status'] != 'recruiting':
        await callback.answer("Рейд уже начался!")
        return
    
    if callback.from_user.id != raid['creator_id']:
        await callback.answer("Только создатель может начать бой!")
        return
    
    if len(raid['players']) < 2:
        await callback.answer("Нужно минимум 2 участника для битвы!")
        return
    
    raid['status'] = 'fighting'
    
    boss = next((b for b in api.get_bosses() if b.id == raid['boss_id']), None)
    if not boss:
        await callback.answer("Ошибка!")
        return
    
    await callback.answer("Битва начинается!")
    
    all_players = api.get_all_players()
    for user_id in raid['players']:
        try:
            for p in all_players:
                if p.user_id == user_id:
                    await callback.bot.send_message(
                        chat_id=p.chat_id,
                        text=f"<b>Битва начинается!</b>\n\n"
                             f"Босс: {boss.name}\n"
                             f"Участников: {len(raid['players'])}\n\n"
                             f"Идёт расчёт результатов..."
                    )
                    break
        except:
            pass
    
    await callback.message.edit_text("<b>Битва началась!</b>\n\nРасчёт результатов...")
    
    battle_result = await perform_raid_battle(raid, boss, callback)
    
    boss_hp = battle_result['boss_hp']
    total_damage = battle_result['total_damage']
    players_names = battle_result['players_names']
    players_damage = battle_result['players_damage']
    
    text = f"<b>Битва с {boss.name}!</b>\n\n"
    text += f"Участники: {', '.join(players_names)}\n"
    
    for i, name in enumerate(players_names):
        if i < len(players_damage):
            text += f"   {name}: {players_damage[i]} урона\n"
    
    text += f"\nОбщий урон: {total_damage}\n"
    
    if boss_hp <= 0:
        reward_per_player = boss.money_reward // len(raid['players'])
        exp_per_player = boss.exp_reward // len(raid['players'])
    
        text += f"\n<b>ПОБЕДА!</b>\n"
        text += f"Каждый игрок получает:\n"
        text += f"{reward_per_player} монет\n"
        text += f"{exp_per_player} опыта"

        achievement_messages = []
        achievement_config = {
            1: {"name": "Убийца Бати Коллектора", "desc": "Вы победили Батю Коллектора в рейде!"},
            2: {"name": "Победитель Кыксика", "desc": "Вы победили Кыксика в рейде!"},
            3: {"name": "Сокрушитель Жабы", "desc": "Вы победили Жабу в рейде!"}
        }

        for user_id in raid['players']:
            for p in all_players:
                if p.user_id == user_id:
                    existing = api.get_user_achievements(p.chat_id, user_id)
                    has_achievement = any(a.name == achievement_config[boss.id]['name'] for a in existing)
                
                    if not has_achievement and boss.id in achievement_config:
                        result = api.give_achievement(
                            chat_id=p.chat_id,
                            user_id=user_id,
                            name=achievement_config[boss.id]['name'],
                            description=achievement_config[boss.id]['desc'],
                            condition=f"Победа над боссом {boss.name}"
                        )
                        if result:
                            achievement_messages.append(f"{p.name} получил достижение '{achievement_config[boss.id]['name']}'!")
                    break
    
        level_up_messages = []
        for user_id in raid['players']:
            for p in all_players:
                if p.user_id == user_id:
                    player = api.get_player(p.chat_id, user_id)
                    if player:
                        player.money += reward_per_player
                        leveled = player.add_exp(exp_per_player)
                        api.update_player(player)
                        if leveled:
                            level_up_messages.append(f"{player.name} ПОВЫСИЛ УРОВЕНЬ ДО {player.level}!")
                    break
    
        if level_up_messages:
            text += "\n\n" + "\n".join(level_up_messages)
        
        for user_id in raid['players']:
            try:
                for p in all_players:
                    if p.user_id == user_id:
                        await callback.bot.send_message(
                            chat_id=p.chat_id,
                            text=f"<b>ПОБЕДА В РЕЙДЕ!</b>\n\n{text}"
                        )
                        break
            except Exception as e:
                print(f"Ошибка отправки результата игроку {user_id}: {e}")
        
        del active_raids[raid_id]
        
    else:
        text += f"\n<b>ПОРАЖЕНИЕ!</b>\n"
        text += f"У босса осталось HP: {boss_hp}\n\n"
        text += f"Можно попробовать снова!"
        
        raid['boss_current_hp'] = boss_hp
        raid['status'] = 'recruiting'
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Начать бой снова",
                        callback_data=f"start_raid_battle_{raid_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Отменить рейд",
                        callback_data=f"cancel_raid_{raid_id}"
                    )
                ]
            ]
        )
        
        for user_id in raid['players']:
            try:
                for p in all_players:
                    if p.user_id == user_id:
                        if user_id == raid['creator_id']:
                            await callback.bot.send_message(
                                chat_id=p.chat_id,
                                text=text,
                                reply_markup=keyboard
                            )
                        else:
                            await callback.bot.send_message(
                                chat_id=p.chat_id,
                                text=text
                            )
                        break
            except Exception as e:
                print(f"Ошибка отправки результата игроку {user_id}: {e}")
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    await callback.answer("Битва завершена!")

@router.callback_query(F.data.startswith("cancel_raid_"))
async def cmd_cancel_raid(callback: types.CallbackQuery):
    raid_id = callback.data.replace("cancel_raid_", "")
    
    if raid_id not in active_raids:
        await callback.answer("Рейд уже завершён!")
        return
    
    raid = active_raids[raid_id]
    
    if callback.from_user.id != raid['creator_id']:
        await callback.answer("Только создатель может отменить рейд!")
        return
    
    all_players = api.get_all_players()
    for user_id in raid['players']:
        if user_id != callback.from_user.id:
            try:
                for p in all_players:
                    if p.user_id == user_id:
                        await callback.bot.send_message(
                            chat_id=p.chat_id,
                            text=f"Рейд был отменён создателем!"
                        )
                        break
            except:
                pass

async def check_and_give_boss_achievements(boss_id, user_id, chat_id, bot):
    achievement_config = {
        1: {
            'name': "Убийца Бати Коллектора",
            'description': "Вы победили Батю Коллектора в рейде!"
        },
        2: {
            'name': "Победитель Кыксика",
            'description': "Вы победили Кыксика в рейде!"
        },
        3: {
            'name': "Сокрушитель Жабы",
            'description': "Вы победили Жабу в рейде!"
        }
    }
    
    if boss_id in achievement_config:
        config = achievement_config[boss_id]
        
        existing_achievements = api.get_user_achievements(chat_id, user_id)
        for ach in existing_achievements:
            if ach.name == config['name']:
                return False
        
        result = api.give_achievement(
            chat_id=chat_id,
            user_id=user_id,
            name=config['name'],
            description=config['description'],
            condition=f"Победа над боссом (ID: {boss_id})"
        )
        return result is not None
    
    return False
    
    del active_raids[raid_id]
    await callback.answer("Рейд отменён!")
    await callback.message.edit_text("Рейд отменён")