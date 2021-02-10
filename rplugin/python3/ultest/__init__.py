import logging

from .handler import HandlerFactory

try:
    import vim  # type: ignore

    HANDLER = None

    def _check_started():
        global HANDLER  # pylint: disable=W0603
        if not HANDLER:
            HANDLER = HandlerFactory.create(vim)

    def _ultest_strategy(*args):
        _check_started()
        HANDLER.strategy(*args)

    def _ultest_run_all(*args):
        _check_started()
        HANDLER.run_all(*args)

    def _ultest_run_nearest(*args):
        _check_started()
        HANDLER.run_nearest(*args)

    def _ultest_run_single(*args):
        _check_started()
        HANDLER.run_single(*args)

    def _ultest_update_positions(*args):
        _check_started()
        HANDLER.update_positions(*args)

    def _ultest_clear_all(*args):
        _check_started()
        HANDLER.clear_all(*args)

    def _ultest_get_nearest_test(*args):
        _check_started()
        return HANDLER.get_nearest_test(*args)


except ImportError:
    from pynvim import Nvim, function, plugin

    try:

        @plugin
        class Ultest:
            def __init__(self, nvim: Nvim):
                self._vim = nvim
                self._handler = None

            @property
            def handler(self):
                if not self._handler:
                    self._handler = HandlerFactory.create(self._vim)
                return self._handler

            @function("_ultest_strategy")
            def _strategy(self, args):
                self.handler.strategy(*args)

            @function("_ultest_run_all")
            def _run_all(self, args):
                self.handler.run_all(*args)

            @function("_ultest_run_nearest")
            def _run_nearest(self, args):
                self.handler.run_nearest(*args)

            @function("_ultest_run_single")
            def _run_single(self, args):
                self.handler.run_single(*args)

            @function("_ultest_update_positions")
            def _update_positions(self, args):
                self.handler.update_positions(*args)

            @function("_ultest_clear_all")
            def _clear_all(self, args):
                self.handler.clear_all(*args)

            @function("_ultest_get_nearest_test", sync=True)
            def _get_nearest_test(self, args):
                return self.handler.get_nearest_test_dict(*args)

    except Exception:
        logging.exception("Error instantiating client")
