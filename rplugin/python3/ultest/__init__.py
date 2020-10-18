from importlib.util import find_spec

import ultest.handler as handler

try:
    import vim  # pylint: disable=E0401

    HANDLER = None

    def _check_started():
        global HANDLER  # pylint: disable=W0603
        if not HANDLER:
            HANDLER = handler.create(vim)

    def _ultest_strategy(*args):
        _check_started()
        HANDLER.strategy(*args)

    def _ultest_run_all(*args):
        _check_started()
        HANDLER.run_all(*args)

    def _ultest_run_nearest(*args):
        _check_started()
        HANDLER.run_nearest(*args)

    def _ultest_clear_old(*args):
        _check_started()
        HANDLER.clear_old(*args)

    def _ultest_set_positions(*args):
        _check_started()
        HANDLER.store_positions(*args)

    def _ultest_get_positions(*args):
        _check_started()
        return HANDLER.get_positions(*args)

    def _ultest_nearest_output(*args):
        _check_started()
        return HANDLER.nearest_output(*args)

    def _ultest_get_output(*args):
        _check_started()
        return HANDLER.get_output(*args)


except ImportError:
    from pynvim import Nvim, function, plugin

    @plugin
    class Ultest:
        def __init__(self, nvim: Nvim):
            self._vim = nvim
            self._handler = None

        def _check_started(self):
            if not self._handler:
                self._handler = handler.create(self._vim)

        @function("_ultest_strategy")
        def _strategy(self, args):
            self._check_started()
            self._handler.strategy(*args)

        @function("_ultest_run_all")
        def _run_all(self, args):
            self._check_started()
            self._handler.run_all(*args)

        @function("_ultest_run_nearest")
        def _run_nearest(self, args):
            self._check_started()
            self._handler.run_nearest(*args)

        @function("_ultest_clear_old")
        def _clear_old(self, args):
            self._check_started()
            self._handler.clear_old(*args)

        @function("_ultest_set_positions")
        def _set_positions(self, args):
            self._check_started()
            self._handler.store_positions(*args)

        @function("_ultest_get_positions", sync=True)
        def _get_positions(self, args):
            self._check_started()
            return self._handler.get_positions(*args)

        @function("_ultest_nearest_output", sync=True)
        def _nearest_output(self, args):
            self._check_started()
            return self._handler.nearest_output(*args)

        @function("_ultest_get_output", sync=True)
        def _get_output(self, args):
            self._check_started()
            return self._handler.get_output(*args)
