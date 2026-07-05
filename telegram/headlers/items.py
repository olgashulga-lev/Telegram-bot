from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import api
from .common_utils import get_player_or_none

router = Router()

@router.message(Command("use"))
async def cmd_use_item(message: types.Message):
    """Использовать предмет из инвентаря"""
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    inventory = api.get_inventory(message.chat.id, message.from_user.id)
    
    if not inventory:
        await message.answer("У вас нет предметов!")
        return
    
    # Фильтруем только используемые предметы (зелья и т.д.)
    usable_items = [i for i in inventory if i.get('type') == 'shop' and i.get('quantity', 0) > 0]
    
    if not usable_items:
        await message.answer("У вас нет предметов для использования!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for item in usable_items:
        # Показываем только зелья здоровья и другие используемые предметы
        if item.get('item_id') in [1, 2, 3, 4]:  # ID предметов
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🔄 {item.get('name')} (x{item.get('quantity')})",
                    callback_data=f"use_item_{item.get('id')}_{item.get('item_id')}"
                )
            ])
    
    if not keyboard.inline_keyboard:
        await message.answer("Нет предметов для использования!")
        return
    
    await message.answer(
        "Выберите предмет для использования:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("use_item_"))
async def cmd_use_item_callback(callback: types.CallbackQuery):
    data = callback.data.split('_')
    if len(data) < 3:
        await callback.answer("Ошибка!")
        return
    
    try:
        inventory_id = int(data[2])
        item_id = int(data[3])
    except ValueError:
        await callback.answer("Ошибка!")
        return
    
    player = api.get_player(callback.message.chat.id, callback.from_user.id)
    if not player:
        await callback.answer("Сначала зарегистрируйтесь!")
        return
    
    # Используем предмет
    if item_id == 1:  # Зелье здоровья
        result = api.use_item_in_battle(callback.message.chat.id, callback.from_user.id, item_id)
        if result:
            await callback.answer(f"💚 +{result['healed']} HP! Текущее HP: {result['new_hp']}")
            await callback.message.edit_text(
                f"✅ Вы использовали зелье здоровья!\n"
                f"💚 Восстановлено: {result['healed']} HP\n"
                f"❤️ Текущее HP: {result['new_hp']}/100"
            )
        else:
            await callback.answer("❌ Не удалось использовать предмет!")
    
    elif item_id == 2:  # Зелье силы
        # Применяем эффект увеличения урона на 5 минут
        duration = 5 * 60  # 5 минут
        api.apply_effect(callback.message.chat.id, callback.from_user.id, 'damage_bonus', 5, duration)
        
        # Удаляем зелье из инвентаря
        inventory = api.get_inventory(callback.message.chat.id, callback.from_user.id)
        item = next((i for i in inventory if i.get('item_id') == item_id), None)
        if item:
            if item.get('quantity', 0) > 1:
                # Уменьшаем количество
                api._make_request("PUT", "inventory/update", data={
                    'inventory_id': item.get('id'),
                    'quantity': item.get('quantity') - 1
                })
            else:
                # Удаляем предмет
                api._make_request("DELETE", f"inventory/remove/{item.get('id')}")
        
        await callback.answer("⚔️ Эффект силы активирован!")
        await callback.message.edit_text(
            f"✅ Вы использовали зелье силы!\n"
            f"⚔️ Урон увеличен на 5\n"
            f"⏱️ Длительность: 5 минут"
        )
    
    elif item_id == 3:  # Амулет удачи
        # Применяем эффект удачи на 10 минут
        duration = 10 * 60  # 10 минут
        api.apply_effect(callback.message.chat.id, callback.from_user.id, 'luck_bonus', 20, duration)
        
        # Удаляем амулет из инвентаря
        inventory = api.get_inventory(callback.message.chat.id, callback.from_user.id)
        item = next((i for i in inventory if i.get('item_id') == item_id), None)
        if item:
            if item.get('quantity', 0) > 1:
                api._make_request("PUT", "inventory/update", data={
                    'inventory_id': item.get('id'),
                    'quantity': item.get('quantity') - 1
                })
            else:
                api._make_request("DELETE", f"inventory/remove/{item.get('id')}")
        
        await callback.answer("🍀 Удача увеличена!")
        await callback.message.edit_text(
            f"✅ Вы использовали амулет удачи!\n"
            f"🍀 Удача увеличена на 20%\n"
            f"⏱️ Длительность: 10 минут"
        )
    
    elif item_id == 4:  # Броня
        # Применяем эффект HP на 10 минут
        duration = 10 * 60  # 10 минут
        api.apply_effect(callback.message.chat.id, callback.from_user.id, 'hp_bonus', 20, duration)
        
        # Удаляем броню из инвентаря
        inventory = api.get_inventory(callback.message.chat.id, callback.from_user.id)
        item = next((i for i in inventory if i.get('item_id') == item_id), None)
        if item:
            if item.get('quantity', 0) > 1:
                api._make_request("PUT", "inventory/update", data={
                    'inventory_id': item.get('id'),
                    'quantity': item.get('quantity') - 1
                })
            else:
                api._make_request("DELETE", f"inventory/remove/{item.get('id')}")
        
        await callback.answer("🛡️ Броня активирована!")
        await callback.message.edit_text(
            f"✅ Вы использовали броню!\n"
            f"🛡️ HP увеличен на 20\n"
            f"⏱️ Длительность: 10 минут"
        )

@router.message(Command("effects"))
async def cmd_show_effects(message: types.Message):
    """Показать активные эффекты"""
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    effects = api.get_active_effects(message.chat.id, message.from_user.id)
    
    if not effects:
        await message.answer("У вас нет активных эффектов!")
        return
    
    text = "⚡ <b>Активные эффекты:</b>\n\n"
    
    effect_names = {
        'hp_bonus': '🛡️ Броня',
        'damage_bonus': '⚔️ Сила',
        'luck_bonus': '🍀 Удача'
    }
    
    for e in effects:
        name = effect_names.get(e.get('effect_type'), e.get('effect_type'))
        minutes = e.get('remaining_seconds', 0) // 60
        seconds = e.get('remaining_seconds', 0) % 60
        text += f"{name}: +{e.get('value')} (осталось {minutes}м {seconds}с)\n"
    
    await message.answer(text)