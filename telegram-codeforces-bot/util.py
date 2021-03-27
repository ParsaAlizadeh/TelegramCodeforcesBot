from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from . import constants
from .database import Database


def score_markup(db: Database, mention: str) -> InlineKeyboardMarkup:
    scores = db.get_scores(mention)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=f'{emoji} {scores[title]}',
                callback_data=f'{mention} {title}'
            ) for title, emoji in constants.emojis.items()
        ]
    ])
