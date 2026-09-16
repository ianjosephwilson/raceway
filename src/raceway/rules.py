from .protocols import ScopeType


def can_depend_on(scope: ScopeType, dep_scope: ScopeType) -> bool:
    if dep_scope == "startup":
        return scope in ("call", "task", "startup")
    elif dep_scope == "task":
        return scope in ("call", "task")
    else:  # call
        return scope == "call"
