import pytest


class TestAuth:
    @pytest.mark.http_request.with_args(session_kv=("user_id", "1"))
    def test_logged_in(self, auth_api):
        assert auth_api.is_logged_in()

    def test_not_logged_in(self, auth_api):
        assert not auth_api.is_logged_in()
