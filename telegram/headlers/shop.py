from aiogram import Router, types, F
from aiogram.filters import Command

import api
from .common_utils import get_player_or_none
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    items = api.get_items()
    shop_items = [i for i in items if i.type == 'shop']
    
    if not shop_items:
        await message.answer("Магазин пуст!")
        return
    
    text = f"<b>Магазин</b>\n Ваш баланс: {player.money}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for item in shop_items:
        text += f"<b>{item.name}</b>\n"
        text += f"   {item.description}\n"
        text += f"   {item.price} монет\n\n"
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"Купить {item.name} ({item.price})",
                callback_data=f"buy_{item.id}"
            )
        ])
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("buy_"))
async def cmd_shop_buy(callback: types.CallbackQuery):
    data = callback.data.split('_')
    if len(data) < 2:
        await callback.answer("Ошибка!")
        return
    
    try:
        item_id = int(data[1])
    except ValueError:
        await callback.answer("Ошибка!")
        return
    
    player = api.get_player(callback.message.chat.id, callback.from_user.id)
    if not player:
        await callback.answer("Сначала зарегистрируйтесь!")
        return
    
    items = api.get_items()
    item = next((i for i in items if i.id == item_id), None)
    
    if not item:
        await callback.answer("Такого предмета нет!")
        return
    
    if player.money < item.price:
        await callback.answer(f"Не хватает денег! Нужно: {item.price}, есть: {player.money}")
        return
    
    # Списываем деньги
    player.money -= item.price
    api.update_player(player)
    
    # ДОБАВЛЯЕМ ПРЕДМЕТ В ИНВЕНТАРЬ
    api.add_item_to_inventory(
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        item_id=item.id,
        item_name=item.name,
        item_type=item.type
    )
    
    await callback.answer(f"✅ Вы купили {item.name}!")
    
    text = f"<b>Магазин</b>\nВаш баланс: {player.money}\n\n✅ Куплено: {item.name}"
    await callback.message.edit_text(text)