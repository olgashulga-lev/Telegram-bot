import asyncio
import configparser

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from headlers.init import register_handlers

config = configparser.ConfigParser()
config.read('config.ini')


try:
    TELEGRAM_API_BASE_URL = config['DEFAULT']['TELEGRAM_API_BASE_URL']
    api = TelegramAPIServer.from_base(TELEGRAM_API_BASE_URL)
    session = AiohttpSession(api=api)
except:
    session = None


# Set up the session if a custom server URL is provided

# Initialize Bot and Dispatcher
bot = Bot(
    token=config['DEFAULT']['TOKEN'],
    default=DefaultBotProperties(parse_mode="HTML"),
    session=session
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def set_commands():
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="registration", description="Создать персонажа"),
        BotCommand(command="avatar", description="Мой профиль"),
        BotCommand(command="inventory", description="Инвентарь"),
        BotCommand(command="achievement", description="Достижения"),
        BotCommand(command="fight", description="Вызвать на дуэль"),
        BotCommand(command="event", description="Мероприятия"),
        BotCommand(command="raid", description="Рейды на боссов"),
        BotCommand(command="shop", description="Магазин"),
        BotCommand(command="dice", description="Игра в кости"),
        BotCommand(command="use", description="Использовать предмет"),
        BotCommand(command="effects", description="Активные эффекты"),
        BotCommand(command="fight_cancel", description="Отменить дуэль"),
    ]
    await bot.set_my_commands(commands)


async def on_startup():
    await set_commands()
    print("Бот запущен!")


async def main():
    register_handlers(dp)

    await on_startup()
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())