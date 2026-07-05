import random
import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import api
from .common_utils import get_player_or_none

router = Router()
active_duels = {}

async def perform_duel(player1, player2, challenger_id, target_id, callback):
    """Выполнить дуэль с 3 раундами и потерей HP"""
    
    # Очищаем истекшие эффекты
    api.clear_expired_effects(callback.message.chat.id, player1.user_id)
    api.clear_expired_effects(callback.message.chat.id, player2.user_id)
    
    # Получаем активные эффекты
    effects1 = api.get_active_effects(callback.message.chat.id, player1.user_id)
    effects2 = api.get_active_effects(callback.message.chat.id, player2.user_id)
    
    # Применяем эффекты к характеристикам
    player1_damage = player1.damage
    player2_damage = player2.damage
    player1_luck = player1.luck
    player2_luck = player2.luck
    player1_hp = player1.hp
    player2_hp = player2.hp
    
    # Применяем бонусы от эффектов
    for e in effects1:
        if e.get('effect_type') == 'damage_bonus':
            player1_damage += e.get('value', 0)
        elif e.get('effect_type') == 'luck_bonus':
            player1_luck += e.get('value', 0) / 100
        elif e.get('effect_type') == 'hp_bonus':
            player1_hp += e.get('value', 0)
    
    for e in effects2:
        if e.get('effect_type') == 'damage_bonus':
            player2_damage += e.get('value', 0)
        elif e.get('effect_type') == 'luck_bonus':
            player2_luck += e.get('value', 0) / 100
        elif e.get('effect_type') == 'hp_bonus':
            player2_hp += e.get('value', 0)
    
    # Сохраняем начальное HP для отображения
    initial_hp1 = player1_hp
    initial_hp2 = player2_hp
    
    text = f"⚔️ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\n\n"
    text += f"👤 {player1.name} ❤️ {player1_hp} HP | ⚔️ {player1_damage} урона\n"
    text += f"👤 {player2.name} ❤️ {player2_hp} HP | ⚔️ {player2_damage} урона\n\n"
    text += f"🎯 <b>Бой идёт до 3 раундов или до смерти!</b>\n"
    text += "═" * 30 + "\n\n"
    
    # 3 раунда или пока кто-то не умрёт
    max_rounds = 3
    round_num = 1
    
    while round_num <= max_rounds and player1_hp > 0 and player2_hp > 0:
        text += f"<b>⚡ РАУНД {round_num}</b>\n"
        
        # Бросок на инициативу (кто первый атакует)
        initiative1 = random.randint(1, 20) + player1_luck * 10
        initiative2 = random.randint(1, 20) + player2_luck * 10
        
        # Расчёт урона
        base_damage1 = random.randint(5, 15) + player1_damage // 3
        base_damage2 = random.randint(5, 15) + player2_damage // 3
        
        # Удача может увеличить урон
        if random.random() < player1_luck:
            base_damage1 = int(base_damage1 * 1.5)
            text += f"🍀 {player1.name} повезло! Критический удар!\n"
        
        if random.random() < player2_luck:
            base_damage2 = int(base_damage2 * 1.5)
            text += f"🍀 {player2.name} повезло! Критический удар!\n"
        
        # Кто атакует первым
        if initiative1 >= initiative2:
            # Игрок 1 атакует первым
            player2_hp -= base_damage1
            if player2_hp <= 0:
                player2_hp = 0
                text += f"⚔️ {player1.name} нанёс {base_damage1} урона → ❤️ {player2_hp}\n"
                text += f"💀 {player2.name} повержен!\n"
                break
            
            # Игрок 2 отвечает
            player1_hp -= base_damage2
            if player1_hp <= 0:
                player1_hp = 0
                text += f"⚔️ {player1.name} нанёс {base_damage1} урона → ❤️ {player2_hp}\n"
                text += f"⚔️ {player2.name} нанёс {base_damage2} урона → ❤️ {player1_hp}\n"
                text += f"💀 {player1.name} повержен!\n"
                break
            
            text += f"⚔️ {player1.name} нанёс {base_damage1} урона → ❤️ {player2_hp}\n"
            text += f"⚔️ {player2.name} нанёс {base_damage2} урона → ❤️ {player1_hp}\n"
        else:
            # Игрок 2 атакует первым
            player1_hp -= base_damage2
            if player1_hp <= 0:
                player1_hp = 0
                text += f"⚔️ {player2.name} нанёс {base_damage2} урона → ❤️ {player1_hp}\n"
                text += f"💀 {player1.name} повержен!\n"
                break
            
            # Игрок 1 отвечает
            player2_hp -= base_damage1
            if player2_hp <= 0:
                player2_hp = 0
                text += f"⚔️ {player2.name} нанёс {base_damage2} урона → ❤️ {player1_hp}\n"
                text += f"⚔️ {player1.name} нанёс {base_damage1} урона → ❤️ {player2_hp}\n"
                text += f"💀 {player2.name} повержен!\n"
                break
            
            text += f"⚔️ {player2.name} нанёс {base_damage2} урона → ❤️ {player1_hp}\n"
            text += f"⚔️ {player1.name} нанёс {base_damage1} урона → ❤️ {player2_hp}\n"
        
        text += "\n"
        round_num += 1
    
    # Определяем победителя
    text += "═" * 30 + "\n\n"
    
    # Переменные для опыта
    exp_for_winner = random.randint(15, 40)  # Победа
    exp_for_loser = random.randint(5, 15)    # Поражение
    
    if player1_hp > player2_hp:
        win_money = random.randint(20, 100)
        player1.money += win_money
        player1.hp = player1_hp
        player2.hp = player2_hp
        
        # Добавляем опыт
        leveled1 = player1.add_exp(exp_for_winner)
        leveled2 = player2.add_exp(exp_for_loser)
        
        api.update_player(player1)
        api.update_player(player2)
        
        text += f"🎉 <b>{player1.name} ПОБЕДИЛ!</b>\n"
        text += f"💰 +{win_money} монет!\n"
        text += f"⭐ +{exp_for_winner} опыта"
        if leveled1:
            text += f" 🎊 {player1.name} ПОВЫСИЛ УРОВЕНЬ ДО {player1.level}!"
        text += f"\n❤️ Осталось HP: {player1_hp}\n"
        
        text += f"\n💔 {player2.name} проиграл\n"
        text += f"⭐ +{exp_for_loser} опыта (за участие)"
        if leveled2:
            text += f" 🎊 {player2.name} ПОВЫСИЛ УРОВЕНЬ ДО {player2.level}!"
        
        if player2_hp <= 0:
            text += f"\n💀 {player2.name} мёртв!"
    
    elif player2_hp > player1_hp:
        win_money = random.randint(20, 100)
        player2.money += win_money
        player1.hp = player1_hp
        player2.hp = player2_hp
        
        leveled1 = player1.add_exp(exp_for_loser)
        leveled2 = player2.add_exp(exp_for_winner)
        
        api.update_player(player1)
        api.update_player(player2)
        
        text += f"🎉 <b>{player2.name} ПОБЕДИЛ!</b>\n"
        text += f"💰 +{win_money} монет!\n"
        text += f"⭐ +{exp_for_winner} опыта"
        if leveled2:
            text += f" 🎊 {player2.name} ПОВЫСИЛ УРОВЕНЬ ДО {player2.level}!"
        text += f"\n❤️ Осталось HP: {player2_hp}\n"
        
        text += f"\n💔 {player1.name} проиграл\n"
        text += f"⭐ +{exp_for_loser} опыта (за участие)"
        if leveled1:
            text += f" 🎊 {player1.name} ПОВЫСИЛ УРОВЕНЬ ДО {player1.level}!"
        
        if player1_hp <= 0:
            text += f"\n💀 {player1.name} мёртв!"
    
    else:
        # Ничья - оба выжили с равным HP
        player1.hp = player1_hp
        player2.hp = player2_hp
        
        # Оба получают немного опыта
        exp_draw = random.randint(10, 20)
        leveled1 = player1.add_exp(exp_draw)
        leveled2 = player2.add_exp(exp_draw)
        
        api.update_player(player1)
        api.update_player(player2)
        
        text += f"🤝 <b>НИЧЬЯ!</b>\n"
        text += f"❤️ У обоих осталось {player1_hp} HP\n"
        text += f"⭐ Оба получают +{exp_draw} опыта!"
        if leveled1:
            text += f" 🎊 {player1.name} ПОВЫСИЛ УРОВЕНЬ ДО {player1.level}!"
        if leveled2:
            text += f" 🎊 {player2.name} ПОВЫСИЛ УРОВЕНЬ ДО {player2.level}!"
    
    # Восстанавливаем HP после боя (но не больше максимума)
    if player1_hp < 0:
        player1_hp = 0
    if player2_hp < 0:
        player2_hp = 0
    
    player1.hp = min(100, player1_hp)
    player2.hp = min(100, player2_hp)
    api.update_player(player1)
    api.update_player(player2)
    
    return text


@router.message(Command("fight"))
async def cmd_duel(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    # Используем ГЛОБАЛЬНЫЙ поиск
    all_players = api.get_all_players_global()
    
    # Фильтруем: убираем самого себя и игроков, которые уже в дуэлях
    available_players = []
    for p in all_players:
        if p.user_id == message.from_user.id:
            continue
        
        # Проверяем, не участвует ли игрок в дуэли
        in_duel = False
        if message.chat.id in active_duels:
            for duel in active_duels[message.chat.id]:
                if duel['player1'] == p.user_id or duel['player2'] == p.user_id:
                    in_duel = True
                    break
        
        if not in_duel:
            available_players.append(p)
    
    if not available_players:
        await message.answer("❌ Нет доступных игроков для дуэли!")
        return
    
    # Создаем клавиатуру со списком игроков
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for p in available_players[:10]:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"⚔️ {p.name} (Ур. {p.level} | ❤️ {p.hp} HP)",
                callback_data=f"duel_select_{p.user_id}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="duel_cancel"
        )
    ])
    
    await message.answer(
        "👥 <b>Выберите противника для дуэли:</b>\n\n"
        f"💰 Ваш баланс: {player.money} монет\n"
        f"❤️ Ваше HP: {player.hp}\n"
        f"⚔️ Ваш урон: {player.damage}\n\n"
        f"⚡ Бой будет длиться до 3 раундов или до смерти!",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("duel_select_"))
async def cmd_duel_select(callback: types.CallbackQuery):
    data = callback.data.split('_')
    
    if len(data) < 3:
        await callback.answer("Ошибка!")
        return
    
    try:
        target_id = int(data[2])
    except ValueError:
        await callback.answer("Ошибка!")
        return
    
    # Проверяем, что вызывающий зарегистрирован
    player = api.get_player(callback.message.chat.id, callback.from_user.id)
    if not player:
        await callback.answer("Сначала зарегистрируйтесь!")
        return
    
    # Проверяем HP игрока
    if player.hp <= 0:
        await callback.answer("💀 Вы мертвы! Восстановите HP через админа или зелья!")
        return
    
    # Ищем цель ГЛОБАЛЬНО (во всех чатах)
    all_players = api.get_all_players_global()
    target = next((p for p in all_players if p.user_id == target_id), None)
    
    if not target:
        await callback.answer("Игрок не найден!")
        return
    
    # Проверяем HP цели
    if target.hp <= 0:
        await callback.answer("💀 Этот игрок мёртв и не может сражаться!")
        return
    
    if target_id == callback.from_user.id:
        await callback.answer("Нельзя вызвать самого себя!")
        return
    
    # Проверяем, не занят ли игрок
    if callback.message.chat.id in active_duels:
        for duel in active_duels[callback.message.chat.id]:
            if duel['player1'] == target_id or duel['player2'] == target_id:
                await callback.answer("Этот игрок уже участвует в дуэли!")
                return
    
    # Создаем дуэль
    if callback.message.chat.id not in active_duels:
        active_duels[callback.message.chat.id] = []
    
    active_duels[callback.message.chat.id].append({
        'player1': callback.from_user.id,
        'player2': target_id,
        'status': 'waiting',
        'challenger_chat_id': callback.message.chat.id,
        'target_chat_id': target.chat_id
    })
    
    # Создаем клавиатуру для принятия дуэли (без зелья)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять дуэль",
                    callback_data=f"accept_duel_{callback.from_user.id}_{target_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отказаться",
                    callback_data=f"refuse_duel_{callback.from_user.id}_{target_id}"
                )
            ]
        ]
    )
    
    # Отправляем сообщение ВЫЗЫВАЮЩЕМУ (подтверждение)
    await callback.message.edit_text(
        f"⚔️ <b>Вы вызвали {target.name} на дуэль!</b>\n\n"
        f"⏳ Ожидайте ответа...\n"
        f"У противника есть 30 секунд, чтобы принять вызов!"
    )
    
    # Отправляем сообщение ПРОТИВНИКУ (запрос на дуэль)
    try:
        await callback.bot.send_message(
            chat_id=target.chat_id,
            text=(
                f"⚔️ <b>ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
                f"👤 <b>{player.name}</b> вызывает вас на дуэль!\n\n"
                f"📊 <b>Статистика вызывающего:</b>\n"
                f"   ❤️ HP: {player.hp}\n"
                f"   ⚔️ Урон: {player.damage}\n"
                f"   🍀 Удача: {int(player.luck * 100)}%\n\n"
                f"📊 <b>Ваша статистика:</b>\n"
                f"   ❤️ HP: {target.hp}\n"
                f"   ⚔️ Урон: {target.damage}\n"
                f"   🍀 Удача: {int(target.luck * 100)}%\n\n"
                f"⏰ У вас есть 30 секунд, чтобы принять вызов!"
            ),
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения противнику: {e}")
        await callback.message.edit_text(
            f"❌ Не удалось отправить вызов {target.name}!\n"
            f"Убедитесь, что бот может писать ему в личные сообщения."
        )
        return
    
    await callback.answer(f"✅ Вызов отправлен {target.name}!")


@router.callback_query(F.data.startswith("refuse_duel_"))
async def cmd_duel_refuse(callback: types.CallbackQuery):
    data = callback.data.split('_')
    if len(data) < 4:
        await callback.answer("Ошибка!")
        return
    
    try:
        challenger_id = int(data[2])
        target_id = int(data[3])
    except ValueError:
        await callback.answer("Ошибка!")
        return
    
    if callback.from_user.id != target_id:
        await callback.answer("Это не ваш вызов!")
        return
    
    # Удаляем дуэль
    if callback.message.chat.id in active_duels:
        for duel in active_duels[callback.message.chat.id][:]:
            if duel['player1'] == challenger_id and duel['player2'] == target_id:
                active_duels[callback.message.chat.id].remove(duel)
                break
    
    await callback.message.edit_text(
        f"❌ {callback.from_user.first_name} отказался от дуэли!"
    )
    await callback.answer("Вы отказались от дуэли")


@router.callback_query(F.data == "duel_cancel")
async def cmd_duel_cancel(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("Выбор отменен")


@router.callback_query(F.data.startswith("accept_duel_"))
async def cmd_duel_accept(callback: types.CallbackQuery):
    data = callback.data.split('_')
    
    if len(data) < 4:
        await callback.answer("Ошибка!")
        return
    
    try:
        challenger_id = int(data[2])
        target_id = int(data[3])
    except ValueError:
        await callback.answer("Ошибка!")
        return
    
    # Проверяем, что это тот, кого вызвали
    if callback.from_user.id != target_id:
        await callback.answer("Это не ваш вызов!")
        return
    
    # Находим дуэль
    duel = None
    duel_key = None
    for key, duels in active_duels.items():
        for d in duels:
            if d['player1'] == challenger_id and d['player2'] == target_id and d['status'] == 'waiting':
                duel = d
                duel_key = key
                break
        if duel:
            break
    
    if not duel:
        await callback.answer("Дуэль уже завершена!")
        return
    
    # Проверяем HP обоих игроков
    player1 = api.get_player(duel['challenger_chat_id'], challenger_id)
    if not player1:
        all_players = api.get_all_players_global()
        player1 = next((p for p in all_players if p.user_id == challenger_id), None)
    
    player2 = api.get_player(callback.message.chat.id, target_id)
    if not player2:
        all_players = api.get_all_players_global()
        player2 = next((p for p in all_players if p.user_id == target_id), None)
    
    if not player1 or not player2:
        await callback.answer("Ошибка! Игроки не найдены!")
        return
    
    if player1.hp <= 0:
        await callback.answer("💀 Вызывающий мёртв! Дуэль отменена.")
        active_duels[duel_key].remove(duel)
        await callback.message.edit_text("❌ Дуэль отменена: вызывающий мёртв!")
        return
    
    if player2.hp <= 0:
        await callback.answer("💀 Вы мертвы! Восстановите HP!")
        return
    
    duel['status'] = 'fighting'
    
    # Удаляем сообщение с вызовом у противника
    await callback.message.edit_text(
        f"⚔️ <b>ДУЭЛЬ НАЧИНАЕТСЯ!</b>\n\n"
        f"👤 {player1.name} ❤️ {player1.hp} HP\n"
        f"👤 {player2.name} ❤️ {player2.hp} HP\n\n"
        f"⏳ Идёт расчёт боя..."
    )
    
    # Отправляем сообщение вызывающему, что дуэль принята
    try:
        await callback.bot.send_message(
            chat_id=duel['challenger_chat_id'],
            text=(
                f"⚔️ <b>{player2.name} ПРИНЯЛ ДУЭЛЬ!</b>\n\n"
                f"Бой начинается!"
            )
        )
    except Exception as e:
        print(f"Ошибка уведомления вызывающего: {e}")
    
    # Задержка для эффекта ожидания
    await asyncio.sleep(2)
    
    # Выполняем бой
    text = await perform_duel(player1, player2, challenger_id, target_id, callback)
    
    # Удаляем дуэль из списка
    active_duels[duel_key].remove(duel)
    
    # Отправляем результат обоим игрокам
    try:
        await callback.bot.send_message(
            chat_id=duel['challenger_chat_id'],
            text=text
        )
    except Exception as e:
        print(f"Ошибка отправки результата вызывающему: {e}")
    
    await callback.message.edit_text(text)
    await callback.answer("Дуэль завершена!")


@router.message(Command("fight_cancel"))
async def cmd_duel_cancel_all(message: types.Message):
    if message.chat.id not in active_duels:
        await message.answer("Нет активных дуэлей!")
        return
    
    removed = False
    for duel in active_duels[message.chat.id][:]:
        if duel['player1'] == message.from_user.id or duel['player2'] == message.from_user.id:
            active_duels[message.chat.id].remove(duel)
            removed = True
    
    if removed:
        await message.answer("❌ Вы отменили свою дуэль.")
    else:
        await message.answer("Вы не участвуете в дуэли.")