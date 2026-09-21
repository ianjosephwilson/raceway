import pytest


@pytest.mark.http_request.with_args(session_kv=('user_id', '1'))
def test_auth_logged_in(auth_api):
    assert auth_api.is_logged_in()


def test_auth_logged_in(auth_api):
    assert not auth_api.is_logged_in()
