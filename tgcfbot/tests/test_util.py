import pytest

from .. import util
from .. import codeforces_api as cf


def test_complete_tags() -> None:
    assert util.complete_tags(['impl']) == ['implementation']
    assert util.complete_tags(['gr']) == ['greedy', 'graphs']
    assert util.complete_tags(['deta']) == []


@pytest.fixture(scope='module')
def sgu_problems() -> list[cf.Problem]:
    return cf.problemset.problems(problemset_name='acmsguru')[0]


def test_sgu_not_valid(sgu_problems: list[cf.Problem]) -> None:
    valid = util.valid_problems(sgu_problems)
    assert len(valid) == 0
