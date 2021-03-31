from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from . import constants
from .database import Database


def score_markup(database: Database, mention: str) -> InlineKeyboardMarkup:
    scores = database.get_scores(mention)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=f'{emoji} {scores[title]}',
                callback_data=f'{mention} {title}'
            ) for title, emoji in constants.emojis.items()
        ]
    ])
