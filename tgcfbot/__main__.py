import logging
import os
from typing import Callable
from uuid import uuid4

from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    InlineQueryHandler,
    CallbackQueryHandler
)

from . import codeforces_api as cf
from . import constants
from . import util
from .database import Database

logging.basicConfig(
    format='[%(levelname)s] %(name)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger('tgcfbot')

token = os.getenv('TOKEN')     # telegram bot token
db_url = os.getenv('DB_URL')   # mongodb url
admins = set(map(int, os.getenv('ADMINS').split(':')))  # telegram id of admins

_commands: dict[str, Callable] = {}
db = Database(db_url=db_url)


def command(cmd: str) -> Callable:
    def wrapper(func: Callable) -> Callable:
        _commands[cmd] = func
        return func

    return wrapper


@command('start')
def start(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Hi!')


@command('register')
def register(update: Update, ctx: CallbackContext) -> None:
    handle = ctx.args[0]
    if handle is None:
        update.message.reply_text(f'handle is empty')
        return
    if handle in constants.limited_handles:
        update.message.reply_text(f'sagzan found')
        return
    try:
        handle = ctx.args[0]
        cf_user, = cf.user.info(handles=[handle])
        db.register_user(update.effective_user, cf_user)
    except cf.APIError:
        update.message.reply_text(f'codeforces api error')
        raise
    else:
        update.message.reply_text(f'register "{handle}"')


@command('gimme')
def gimme(update: Update, ctx: CallbackContext) -> None:
    tags = []
    for q in ctx.args:
        tags += [tag for tag in constants.tags if tag.startswith(q)]

    problem_filter = {}
    if tags:
        tag_list = '", "'.join(tags)
        update.message.reply_text(text=f'looking for problems with tags: "{tag_list}"')
        problem_filter['tags'] = {
            '$all': tags
        }

    if cf_user := db.get_cf_user(update.effective_user.id):
        submissions = cf.user.status(handle=cf_user.handle)
        solved = [s.problem.mention for s in submissions if s.verdict == cf.Verdict.OK]
        problem_filter['_id'] = {'$nin': solved}
        if cf_user.rating:
            problem_filter['rating'] = {
                '$exists': True,
                '$gte': cf_user.rating - 100,
                '$lte': cf_user.rating + 300
            }
        else:
            problem_filter['rating'] = {
                '$exists': True,
                '$lte': 1800
            }

    problem = db.sample_problem(problem_filter)
    update.message.reply_text(
        text=problem.html,
        parse_mode='HTML',
        reply_markup=util.score_markup(db, problem.mention),
        disable_web_page_preview=True,
    )


@command('cache')
def cache_cmd(update: Update, _: CallbackContext) -> None:
    if update.effective_user.id in admins:
        # TODO: Update problems
        update.message.reply_text('cache done')


def inline_query(update: Update, _: CallbackContext) -> None:
    query = update.inline_query.query
    problems = db.query_problem(query, max_count=10)
    result = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=problem.mention,
            description=problem.display_name,
            thumb_url='https://sta.codeforces.com/s/54849/images/codeforces-telegram-square.png',
            input_message_content=InputTextMessageContent(
                message_text=problem.html,
                parse_mode='HTML',
                disable_web_page_preview=True,
            ),
            reply_markup=util.score_markup(db, problem.mention),
        )
        for problem in problems
    ]

    update.inline_query.answer(result, cache_time=10)  # TODO: change 10 to higher on deploy


def callback_query(update: Update, _: CallbackContext) -> None:
    query = update.callback_query

    try:
        mention, title = query.data.split()
        assert title in constants.emojis.keys(), ValueError('not registered emoji')
        flag = db.toggle_score(mention, title, query.from_user.id)

        # Note: this is a wrong behavior
        # client can send bad callback query data and
        # then bot add scoreboard of a problem to the
        # message of other problem
        query.edit_message_reply_markup(
            reply_markup=util.score_markup(db, mention)
        )

        if flag:
            query.answer(text=f'you vote {constants.emojis[title]} for {mention}')
        else:
            query.answer(text=f'you took vote {constants.emojis[title]} for {mention}')

    except:
        query.answer(text='something goes wrong')
        raise


def main() -> None:
    # db.insert_problems(cache.problems)  # TODO: uncomment this on deploy

    updater = Updater(token)
    dispatcher = updater.dispatcher

    for cmd, callback in _commands.items():
        dispatcher.add_handler(CommandHandler(cmd, callback))

    dispatcher.add_handler(InlineQueryHandler(inline_query))
    dispatcher.add_handler(CallbackQueryHandler(callback_query))

    updater.start_polling()
    updater.idle()

    db.close()


if __name__ == '__main__':
    main()
