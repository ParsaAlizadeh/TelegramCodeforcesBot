# pylint: disable=invalid-name

from typing import Any, Iterable, NamedTuple, get_origin, get_args

import requests


def is_namedtuple(cls: type) -> bool:
    return hasattr(cls, '__annotations__')


def from_json(cls: type, data: Any) -> "cls":
    if (orig := get_origin(cls)) in (list, tuple):
        assert len(get_args(cls)) == 1, 'empty or multiple args for list/tuple'
        return orig(from_json(get_args(cls)[0], x) for x in data)

    if is_namedtuple(cls):
        for key, typ in cls.__annotations__.items():
            if key in data:
                data[key] = from_json(typ, data[key])
        return cls(**data)

    return cls(data)


def to_json(obj: Any) -> Any:
    if isinstance(obj, list):
        return [to_json(x) for x in obj]

    if is_namedtuple(obj.__class__):
        result = {}
        for key, value in obj._asdict().items():
            if value is None:
                continue
            result[key] = to_json(value)
        return result

    return obj


class User(NamedTuple):
    handle: str
    contribution: int
    lastOnlineTimeSeconds: int
    registrationTimeSeconds: int
    friendOfCount: int
    avatar: str
    titlePhoto: str
    rank: str = None
    rating: int = None
    maxRank: str = None
    maxRating: int = None
    email: str = None
    vkId: str = None
    openId: str = None
    firstName: str = None
    lastName: str = None
    country: str = None
    city: str = None
    organization: str = None


class RatingChange(NamedTuple):
    contestId: int
    contestName: str
    handle: str
    rank: int
    # ^ This field contains user rank on the moment of rating update.
    # If afterwards rank changes (e.g. someone get disqualified),
    # this field will not be update and will contain old rank.
    ratingUpdateTimeSeconds: int
    oldRating: int
    newRating: int


class ContestType:
    CF = 'CF'
    IOI = 'IOI'
    ICPC = 'ICPC'


class ContestPhase:
    BEFORE = 'BEFORE'
    CODING = 'CODING'
    PENDING_SYSTEM_TEST = 'PENDING_SYSTEM_TEST'
    SYSTEM_TEST = 'SYSTEM_TEST'
    FINISHED = 'FINISHED'


class Contest(NamedTuple):
    id: int
    name: str
    type: str   # ContestType
    phase: str  # ContestPhase
    frozen: bool
    durationSeconds: int
    startTimeSeconds: int = None
    relativeTimeSeconds: int = None
    preparedBy: str = None
    websiteUrl: str = None
    description: str = None
    difficulty: int = None
    kind: str = None
    icpcRegion: str = None
    country: str = None
    city: str = None
    season: str = None


class Member(NamedTuple):
    handle: str


class ParticipantType:
    CONTESTANT = 'CONTESTANT'
    PRACTICE = 'PRACTICE'
    VIRTUAL = 'VIRTUAL'
    MANAGER = 'MANAGER'
    OUT_OF_COMPETITION = 'OUT_OF_COMPETITION'


class Party(NamedTuple):
    members: tuple[Member]
    participantType: str    # ParticipantType
    ghost: bool
    contestId: int = None
    teamId: int = None
    teamName: str = None
    room: int = None
    startTimeSeconds: int = None


class ProblemType:
    PROGRAMMING = 'PROGRAMMING'
    QUESTION = 'QUESTION'


class Problem(NamedTuple):
    index: str
    name: str
    type: str   # ProblemType
    tags: tuple[str]
    contestId: int = None
    problemsetName: str = None
    points: float = None
    rating: int = None

    @property
    def link(self):
        return f'https://codeforces.com/problemset/problem/{self.contestId}/{self.index}'

    @property
    def mention(self):
        return f'{self.contestId}{self.index}'

    @property
    def display_name(self):
        return f'{self.mention} - {self.name} ' + \
               ('(no rating)' if self.rating is None else f'({self.rating})')

    @property
    def html(self):
        return f'<a href="{self.link}">{self.display_name}</a>'


class ProblemStatistics(NamedTuple):
    index: str
    solvedCount: int
    contestId: int = None


class Verdict:
    FAILED = 'FAILED'
    OK = 'OK'
    PARTIAL = 'PARTIAL'
    COMPILATION_ERROR = 'COMPILATION_ERROR'
    RUNTIME_ERROR = 'RUNTIME_ERROR'
    WRONG_ANSWER = 'WRONG_ANSWER'
    PRESENTATION_ERROR = 'PRESENTATION_ERROR'
    TIME_LIMIT_EXCEEDED = 'TIME_LIMIT_EXCEEDED'
    MEMORY_LIMIT_EXCEEDED = 'MEMORY_LIMIT_EXCEEDED'
    IDLENESS_LIMIT_EXCEEDED = 'IDLENESS_LIMIT_EXCEEDED'
    SECURITY_VIOLATED = 'SECURITY_VIOLATED'
    CRASHED = 'CRASHED'
    INPUT_PREPARATION_CRASHED = 'INPUT_PREPARATION_CRASHED'
    CHALLENGED = 'CHALLENGED'
    SKIPPED = 'SKIPPED'
    TESTING = 'TESTING'
    REJECTED = 'REJECTED'


class Submission(NamedTuple):
    id: int
    creationTimeSeconds: int
    relativeTimeSeconds: int
    problem: Problem
    author: Party
    programmingLanguage: str
    verdict: str    # Verdict
    testset: str
    passedTestCount: int
    timeConsumedMillis: int
    memoryConsumedBytes: int
    contestId: int = None
    points: float = None


class ProblemResultType:
    PRELIMINARY = 'PRELIMINARY'
    FINAL = 'FINAL'


class ProblemResult(NamedTuple):
    points: float
    rejectedAttemptCount: int
    type: str   # ProblemResultType
    penalty: int = None
    bestSubmissionTimeSeconds: int = None


class RanklistRow(NamedTuple):
    party: Party
    rank: int
    points: float
    penalty: int
    successfulHackCount: int
    unsuccessfulHackCount: int
    problemResults: tuple[ProblemResult]
    lastSubmissionTimeSeconds: int = None


class APIError(Exception):
    pass


def send_request(method: str, params: dict) -> dict:
    response = requests.get(
        url=f'https://codeforces.com/api/{method}',
        params=params
    )
    values = response.json()
    if values['status'] == 'FAILED':
        raise APIError(values['comment'])
    return values['result']


class contest:
    @staticmethod
    def all(*, gym: bool = None) -> list[Contest]:
        params = {}
        if gym is not None:
            params['gym'] = gym
        result = send_request(method='contest.list', params=params)
        return from_json(list[Contest], result)

    @staticmethod
    def rating_changes(*, contest_id: int) -> list[RatingChange]:
        params = {'contestId': contest_id}
        result = send_request(method='contest.ratingChanges', params=params)
        return from_json(list[RatingChange], result)

    @staticmethod
    def standings(*, contest_id: int,
                  from_: int = None,
                  count: int = None,
                  handles: Iterable[str] = None,
                  room: int = None,
                  show_unofficial: bool = None) -> tuple[Contest, list[Problem], list[RanklistRow]]:
        params = {'contestId': contest_id}
        if from_ is not None:
            params['from'] = from_
        if count is not None:
            params['count'] = count
        if handles is not None:
            params['handles'] = ';'.join(handles)
        if room is not None:
            params['room'] = room
        if show_unofficial is not None:
            params['showUnofficial'] = show_unofficial
        result = send_request(method='contest.standings', params=params)
        return (
            from_json(Contest, result['contest']),
            from_json(list[Problem], result['problems']),
            from_json(list[RanklistRow], result['rows']),
        )

    @staticmethod
    def status(*,
            contest_id: int,
            handle: str = None,
            from_: int = None,
            count: int = None) -> list[Submission]:
        params = {'contestId': contest_id}
        if handle is not None:
            params['handle'] = handle
        if from_ is not None:
            params['from'] = from_
        if count is not None:
            params['count'] = count
        result = send_request(method='contest.status', params=params)
        return from_json(list[Submission], result)


class problemset:
    @staticmethod
    def problems(*,
            tags: Iterable[str] = None,
            problemset_name: str = None
        ) -> tuple[list[Problem], list[ProblemStatistics]]:
        params = {}
        if tags is not None:
            params['tags'] = ';'.join(tags)
        if problemset_name is not None:
            params['problemsetName'] = problemset_name
        result = send_request(method='problemset.problems', params=params)
        return (
            from_json(list[Problem], result['problems']),
            from_json(list[ProblemStatistics], result['problemStatistics']),
        )

    @staticmethod
    def recent_status(*, count: int, problemset_name: str = None) -> list[Submission]:
        params = {'count': count}
        if problemset_name is not None:
            params['problemsetName'] = problemset_name
        result = send_request(method='problemset.recentStatus', params=params)
        return from_json(list[Submission], result)


class user:
    @staticmethod
    def info(*, handles: Iterable[str]) -> list[User]:
        params = {'handles': ';'.join(handles)}
        result = send_request(method='user.info', params=params)
        return from_json(list[User], result)

    @staticmethod
    def rated_list(*, active_only: bool = None) -> list[User]:
        params = {}
        if active_only is not None:
            params['activeOnly'] = active_only
        result = send_request(method='user.ratedList', params=params)
        return from_json(list[User], result)

    @staticmethod
    def rating(*, handle: str) -> list[RatingChange]:
        result = send_request(method='user.rating', params={'handle': handle})
        return from_json(list[RatingChange], result)

    @staticmethod
    def status(*, handle: str, from_: int = None, count: int = None) -> list[Submission]:
        params = {'handle': handle}
        if from_ is not None:
            params['from'] = from_
        if count is not None:
            params['count'] = count
        result = send_request(method='user.status', params=params)
        return from_json(list[Submission], result)
