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

            HANDLER = HandlerFactory.create(vim)

    def _ultest_run_nearest(*args):
        _check_started()
        HANDLER.run_nearest(*args)

    def _ultest_run_single(*args):
        _check_started()
        HANDLER.run_single(*args)

    def _ultest_run_last(*args):
        _check_started()
        HANDLER.run_last(*args)

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

    def _ultest_external_start(*args):
        _check_started()
        return HANDLER.external_start(*args)

    def _ultest_external_result(*args):
        _check_started()
        return HANDLER.external_result(*args)

    def _ultest_safe_split(*args):
        _check_started()
        return HANDLER.safe_split(*args)

    def _ultest_clear_results(*args):
        _check_started()
        return HANDLER.clear_results(*args)


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

                self._handler = HandlerFactory.create(self._vim)
            return self._handler

        @function("_ultest_run_nearest", sync=True)
        def _run_nearest(self, args):
            self.handler.run_nearest(*args)

        @function("_ultest_run_single", sync=True)
        def _run_single(self, args):
            self.handler.run_single(*args)

        @function("_ultest_run_last", allow_nested=True)
        def _run_last(self, args):
            self.handler.run_last(*args)

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

        @function("_ultest_external_start", allow_nested=True)
        def _external_start(self, args):
            return self.handler.external_start(*args)

        @function("_ultest_external_result", allow_nested=True)
        def _external_result(self, args):
            return self.handler.external_result(*args)

        @function("_ultest_safe_split", sync=True)
        def _safe_split(self, args):
            return self.handler.safe_split(*args)

        @function("_ultest_clear_results", sync=True)
        def _clear_results(self, args):
            return self.handler.clear_results(*args)
