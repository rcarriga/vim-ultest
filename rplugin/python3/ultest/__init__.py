import inspect
import os

if os.getenv("ULTEST_DEBUG") or os.getenv("ULTEST_DEBUG_PORT"):
    import debugpy

    debugpy.listen(int(os.getenv("ULTEST_DEBUG_PORT") or 5678))
    debugpy.wait_for_client()


try:
    import vim  # type: ignore

    HANDLER = None

    def _check_started():
        global HANDLER  # pylint: disable=W0603
        if not HANDLER:
            from .handler import HandlerFactory
            from .logging import create_logger

            logger = create_logger()
            HANDLER = HandlerFactory.create(vim, logger)

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

    def _ultest_get_nearest_test(*args):
        _check_started()
        return HANDLER.get_nearest_test_dict(*args)

    def _ultest_get_attach_script(*args):
        _check_started()
        return HANDLER.get_attach_script(*args)

    def _ultest_stop_test(*args):
        _check_started()
        return HANDLER.stop_test(*args)


except ImportError:
    from pynvim import Nvim, function, plugin

    @plugin
    class Ultest:
        def __init__(self, nvim: Nvim):
            self._vim = nvim
            self._handler = None

        @property
        def handler(self):
            if not self._handler:
                from .handler import HandlerFactory
                from .logging import create_logger

                self._handler = HandlerFactory.create(self._vim, create_logger())
            return self._handler

        @function("_ultest_strategy", allow_nested=True)
        def _strategy(self, args):
            self.handler.strategy(*args)

        @function("_ultest_run_all", allow_nested=True)
        def _run_all(self, args):
            self.handler.run_all(*args)

        @function("_ultest_run_nearest", allow_nested=True)
        def _run_nearest(self, args):
            self.handler.run_nearest(*args)

        @function("_ultest_run_single", allow_nested=True)
        def _run_single(self, args):
            self.handler.run_single(*args)

        @function("_ultest_update_positions", allow_nested=True)
        def _update_positions(self, args):
            self.handler.update_positions(*args)

        @function("_ultest_get_nearest_test", sync=True)
        def _get_nearest_test(self, args):
            return self.handler.get_nearest_test_dict(*args)

        @function("_ultest_get_attach_script", sync=True)
        def _get_attach_script(self, args):
            return self.handler.get_attach_script(*args)

        @function("_ultest_stop_test", allow_nested=True)
        def _stop_test(self, args):
            return self.handler.stop_test(*args)
