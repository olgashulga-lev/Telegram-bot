import random
from aiogram import Router, types
from aiogram.filters import Command

import api
from .common_utils import get_player_or_none

router = Router()

@router.message(Command("dice"))
async def cmd_dice(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    bet = 10
    if player.money < bet:
        await message.answer(f"У вас недостаточно денег! Нужно: {bet}, есть: {player.money}")
        return
    
    player_dice = random.randint(1, 6)
    bot_dice = random.randint(1, 6)
    
    text = f"""
<b>Игра в кости</b>
Ставка: {bet} монет

Ваш бросок: {player_dice}
Бросок бота: {bot_dice}
    """
    
    if player_dice > bot_dice:
        win = bet * 2
        player.money += win
        api.update_player(player)
        text += f"\n<b>Вы победили!</b> +{win} монет!"
    elif player_dice < bot_dice:
        player.money -= bet
        api.update_player(player)
        text += f"\n<b>Вы проиграли!</b> -{bet} монет!"
    else:
        text += "\n<b>Ничья!</b> Ставка возвращена."
    
    await message.answer(text)


@router.message(Command("dice_big"))
async def cmd_dice_big(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите ставку: /dice_big 50")
        return
    
    try:
        bet = int(args[1])
        if bet <= 0:
            await message.answer("Ставка должна быть положительной!")
            return
    except ValueError:
        await message.answer("Введите число!")
        return
    
    if player.money < bet:
        await message.answer(f"У вас недостаточно денег! Нужно: {bet}, есть: {player.money}")
        return
    
    player_dice = random.randint(1, 6)
    bot_dice = random.randint(1, 6)
    
    text = f"""
<b>Игра в кости (большая ставка)</b>
Ставка: {bet} монет

Ваш бросок: {player_dice}
Бросок бота: {bot_dice}
    """
    
    if player_dice > bot_dice:
        win = bet * 2
        player.money += win
        api.update_player(player)
        text += f"\n<b>Вы победили!</b> +{win} монет!"
    elif player_dice < bot_dice:
        player.money -= bet
        api.update_player(player)
        text += f"\n<b>Вы проиграли!</b> -{bet} монет!"
    else:
        text += "\n<b>Ничья!</b> Ставка возвращена."
    
    await message.answer(text)