import pytest

from .. import codeforces_api as cf


class TestProblems:
    @pytest.fixture(scope='class')
    def problems(self) -> list[cf.Problem]:
        return cf.problemset.problems()[0]

    def test_count_problems(self, problems: list[cf.Problem]) -> None:
        assert len(problems) >= 6000

    def test_type_problems(self, problems: list[cf.Problem]) -> None:
        assert all(isinstance(x, cf.Problem) for x in problems)

    def test_sample_problem(self, problems: list[cf.Problem]) -> None:
        problem, = [x for x in problems if x.mention == '1497A']
        assert problem.contestId == 1497
        assert problem.index == 'A'
        assert problem.name == 'Meximization'
        assert problem.rating == 800
        assert problem.link == 'https://codeforces.com/problemset/problem/1497/A'


class TestUsers:
    def test_multiple_users(self):
        users = cf.user.info(handles=['tourist', 'Benq', 'Petr'])
        assert len(users) == 3

    def test_available_user(self):
        user, = cf.user.info(handles=['AaParsa'])
        assert user.rating == 2297
        assert user.firstName == 'Parsa'
        assert user.lastName == 'Alizadeh'

    def test_none_rating(self):
        user, = cf.user.info(handles=['vjudge4'])
        assert user.rating is None

    def test_wrong_user(self):
        with pytest.raises(cf.APIError):
            cf.user.info(handles=['pi'])
