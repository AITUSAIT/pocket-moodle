import asyncio


class Suspendable:
    def __init__(self, target):
        self._target = target
        self._can_run = asyncio.Event()
        self._can_run.set()
        self._task = asyncio.ensure_future(self)

    def __await__(self):
        target_iter = self._target.__await__()
        iter_send, iter_throw = target_iter.send, target_iter.throw
        send, message = iter_send, None
        while True:
            try:
                while not self._can_run.is_set():
                    yield from self._can_run.wait().__await__()  # pylint: disable=no-member
            except BaseException as err:
                send, message = iter_throw, err

            try:
                signal = send(message)
            except StopIteration as err:
                return err.value
            send = iter_send
            try:
                message = yield signal
            except BaseException as err:
                send, message = iter_throw, err

    def suspend(self):
        self._can_run.clear()

    def is_suspended(self):
        return not self._can_run.is_set()

    def resume(self):
        self._can_run.set()

    def get_task(self):
        return self._task
