from aiogram import Router, types
from aiogram.filters import Command

import api
from .common_utils import get_player_or_none

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    text = """
<b>Привет! Я МеханоБот!</b>

Я помогу тебе и твоим друзьям играть в интересную игру!

<b>Основные команды:</b>
/start - показать это сообщение
/help - помощь по командам
/registration - создать своего персонажа
/avatar - посмотреть своего персонажа
/inventory - посмотреть инвентарь
/fight - вызвать на дуэль (ответь на сообщение)
/task - посмотреть задания
/event - посмотреть мероприятия
/raid - посмотреть боссов
/achievement - посмотреть достижения
/shop - магазин предметов
/dice - игра в кости
    """
    await message.answer(text)


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = """
<b>Помощь по МеханоБоту</b>

<b>Персонаж</b>
/registration - создать персонажа
/avatar - посмотреть характеристики
/inventory - посмотреть инвентарь

<b>Бои</b>
/fight - ответьте на сообщение игрока, чтобы вызвать на дуэль

<b>Мероприятия</b>
/event - посмотреть мероприятия
/event_create - создать мероприятие

<b>Рейды</b>
/raid - посмотреть список боссов

<b>Достижения</b>
/achievement - посмотреть свои достижения

<b>Магазин</b>
/shop - купить предметы
    """
    await message.answer(text)