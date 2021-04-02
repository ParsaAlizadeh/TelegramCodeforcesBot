from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from . import constants
from . import codeforces_api as cf
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


def complete_tags(queries: list[str]) -> list[str]:
    tags = []
    for query in queries:
        if len(query) > 1:
            tags += [t for t in constants.tags if t.startswith(query)]
    return tags


def valid_problems(problems: list[cf.Problem]) -> list[cf.Problem]:
    return [
        problem for problem in problems
        if problem.contestId is not None and problem.contestId < 100000
    ]
