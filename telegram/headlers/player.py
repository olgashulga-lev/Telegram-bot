from aiogram import Router, types
from aiogram.filters import Command
import api
from .common_utils import get_player_or_none

router = Router()

@router.message(Command("avatar"))
async def cmd_avatar(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    current_level = player.level
    max_level = player.get_max_level()
    
    if current_level < max_level:
        exp_for_next = player.get_exp_for_next_level()
        exp_text = f"Опыт: {player.exp}/{exp_for_next}"
    else:
        exp_text = "МАКСИМУМ!"
    
    text = f"""
<b>{player.name}</b>

Уровень: {player.level}/30
{exp_text}

HP: {player.hp}/100
Урон: {player.damage}
Удача: {int(player.luck * 100)}
Деньги: {player.money}
"""
    try:
        with open(player.photo, 'rb') as photo:
            await message.answer_photo(photo, caption=text)
    except:
        await message.answer(text)

@router.message(Command("inventory"))
async def cmd_inventory(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    inventory = api.get_inventory(message.chat.id, message.from_user.id)
    
    if not inventory:
        await message.answer(f"<b>Инвентарь {player.name}:</b>\n\nПока пуст...")
        return
    
    text = f"<b>Инвентарь {player.name}:</b>\n\n"
    
    items_by_type = {}
    for item in inventory:
        item_type = item.get('type', 'Прочее')
        if item_type not in items_by_type:
            items_by_type[item_type] = []
        items_by_type[item_type].append(item)
    
    for item_type, items in items_by_type.items():
        text += f"<b>{item_type}:</b>\n"
        for item in items:
            text += f"{item['name']} x{item['quantity']}\n"
        text += "\n"
    
    await message.answer(text)

@router.message(Command("achievement"))
async def cmd_achievement(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    achievements = api.get_user_achievements(message.chat.id, message.from_user.id)
    
    if not achievements:
        await message.answer(f"<b>Достижения {player.name}:</b>\n\nПока нет достижений...")
        return
    
    text = f"<b>Достижения {player.name}:</b>\n\n"
    
    for ach in achievements[:10]:
        text += f"<b>{ach.name}</b>\n"
        text += f"   {ach.description}\n\n"
    
    if len(achievements) > 10:
        text += f"\n... и еще {len(achievements) - 10} достижений"
    
    await message.answer(text)