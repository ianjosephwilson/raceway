"""
Example of testing a service.
"""

import pytest

from raceway.testing import IAuth


class TestAuth:

    def test_factory(self, auth_api: IAuth):
        assert auth_api and auth_api.is_logged_in and callable(auth_api.is_logged_in)

    @pytest.mark.http_request.with_args(session_kv=("user_id", "1"))
    def test_logged_in(self, auth_api: IAuth):
        assert auth_api.is_logged_in()

    def test_not_logged_in(self, auth_api: IAuth):
        assert not auth_api.is_logged_in()
