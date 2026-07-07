from aiogram import Dispatcher

from . import common
from . import registration
from . import player
from . import fight
from . import event
from . import raid
from . import games
from . import shop
from . import items


def register_handlers(dp: Dispatcher):
    dp.include_routers(
        common.router,
        registration.router,
        player.router,
        fight.router,
        event.router,
        raid.router,
        games.router,
        shop.router,
        items.router,
    )