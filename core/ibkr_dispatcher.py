# core/ibkr_dispatcher.py

import threading
from collections import defaultdict

class IBKRDispatcher:
    """
    用于统一管理 IBKR 回调响应和请求编号。
    支持多类型请求（tick、contract、historical）的一致回调注册和同步等待。
    """
    def __init__(self):
        self._req_id = 1000
        self._handlers = {}         # reqId -> callback
        self._events = {}           # reqId -> threading.Event
        self._results = defaultdict(list)  # reqId -> collected data list

    def next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def register(self, req_id: int, handler=None, use_event=True):
        if handler:
            self._handlers[req_id] = handler
        if use_event:
            self._events[req_id] = threading.Event()

    def set_result(self, req_id: int, data):
        self._results[req_id].append(data)

    def wait(self, req_id: int, timeout: int = 10) -> list:
        event = self._events.get(req_id)
        if event:
            event.wait(timeout)
        return self._results.get(req_id, [])

    def signal_done(self, req_id: int):
        if req_id in self._events:
            self._events[req_id].set()

    def dispatch(self, req_id: int, *args):
        handler = self._handlers.get(req_id)
        if handler:
            handler(*args)

    def clear(self, req_id: int):
        self._handlers.pop(req_id, None)
        self._events.pop(req_id, None)
        self._results.pop(req_id, None)

    def reset(self):
        self._handlers.clear()
        self._events.clear()
        self._results.clear()
        self._req_id = 1000
