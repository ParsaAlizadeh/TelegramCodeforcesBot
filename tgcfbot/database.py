import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from telegram import User

from . import codeforces_api as cf
from . import constants

logger = logging.getLogger('database')


class Database:
    def __init__(self, db_url):
        self.client = MongoClient(db_url)
        self.users: Collection = self.client.tgcfbot.users
        self.problems: Collection = self.client.tgcfbot.problems
        self.scores: Collection = self.client.tgcfbot.scores

    def register_user(self, tg_user: User, cf_user: cf.User) -> None:
        self.users.update_one(
            filter={"tg_user.id": tg_user.id},
            update={"$set": {
                "tg_user": {"id": tg_user.id, "fullname": tg_user.full_name},
                "cf_user": cf.to_json(cf_user)
            }},
            upsert=True
        )

    def get_cf_user(self, tg_id: int) -> Optional[cf.User]:
        document = self.users.find_one({"tg_user.id": tg_id})
        return document and cf.from_json(cf.User, document['cf_user'])

    def insert_problems(self, problems: list[cf.Problem]) -> int:
        def _get_doc(problem: cf.Problem):
            doc = cf.to_json(problem)
            doc['_id'] = problem.mention
            return doc

        already = set(doc['_id'] for doc in self.problems.find(
            filter={'_id': {'$in': [p.mention for p in problems]}},
            projection={'_id': True}
        ))

        new_problems = [p for p in problems if p.mention not in already]

        if new_problems:
            self.problems.insert_many(
                documents=[_get_doc(p) for p in new_problems],
                ordered=False
            )
            init_score = {title: [] for title in constants.emojis}
            self.scores.insert_many(
                documents=[{'_id': p.mention, **init_score} for p in new_problems],
                ordered=False
            )

        logger.info('%d new problems inserted', len(new_problems))
        return len(new_problems)

    def sample_problem(self, filter_: dict) -> Optional[cf.Problem]:
        if filter_ is None:
            filter_ = {}
        doc, = list(self.problems.aggregate([
            {'$match': filter_},
            {'$project': {'_id': False}},
            {'$sample': {'size': 1}}
        ]))
        return cf.from_json(cf.Problem, doc)

    def query_problem(self, query: str, max_count: int = 10) -> list[cf.Problem]:
        docs = self.problems.find(
            filter={'$or': [
                {'_id': query},
                {'$text': {'$search': f'"{query}"'}}
            ]},
            projection={'_id': False}
        ).limit(max_count)
        return [cf.from_json(cf.Problem, p) for p in docs]

    def get_problem(self, mention: str) -> Optional[cf.Problem]:
        doc = self.problems.find_one(
            filter={'_id': mention},
            projection={'_id': False}
        )
        return doc and cf.from_json(cf.Problem, doc)

    def get_scores(self, mention: str) -> dict[str, int]:
        docs = list(self.scores.aggregate([
            {'$match': {'_id': mention}},
            {'$set': {title: {'$size': f'${title}'} for title in constants.emojis}},
            {'$project': {'_id': False}}
        ]))
        if not docs:
            return {title: 0 for title in constants.emojis}
        return docs[0]

    def toggle_score(self, mention: str, title: str, tg_id: int) -> bool:
        if self.get_problem(mention) is None:
            raise ValueError(f'no such {mention} problem')
        if self.scores.find_one(filter={'_id': mention, title: tg_id}):
            self.scores.update_one(
                filter={'_id': mention},
                update={'$pull': {title: tg_id}}
            )
            return False
        self.scores.update_one(
            filter={'_id': mention},
            update={'$push': {title: tg_id}}
        )
        return True

    def close(self):
        self.client.close()
        logger.info('client closed')
