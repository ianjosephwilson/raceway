"""
Examples of wrapping application callables that inject services.
"""

import pytest

from raceway.testing import IAuth, HTTPUnauthorized


@pytest.fixture()
def inject_then_call(injector_api, container_api, http_request):
    def _inject_then_call(func, **overrides):
        wrapped = injector_api.wrap_in_inject(
            func, validate_with_container=container_api
        )
        return wrapped(container_api, task=http_request, **overrides)

    return _inject_then_call


def account(auth_api: IAuth, skip_check: bool = False) -> str | Exception:
    if not skip_check and not auth_api.is_logged_in():
        return HTTPUnauthorized()
    else:
        return "OK"


class TestAccount:
    def test_unauthorized(self, inject_then_call):
        assert isinstance(inject_then_call(account), HTTPUnauthorized)

    @pytest.mark.http_request.with_args(session_kv=("user_id", "1"))
    def test_authorized(self, inject_then_call):
        assert isinstance(inject_then_call(account), str)

    def test_unauthorized_skip(self, inject_then_call):
        assert isinstance(inject_then_call(account, skip_check=True), str)
