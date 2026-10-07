from contextvars import ContextVar

request_context = ContextVar("request_id", default=None)
