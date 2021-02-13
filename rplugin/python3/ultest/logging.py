import logging
import os
import tempfile

_logger_name = "ultest"


class UltestLogger(logging.Logger):
    def fdebug(self, fstr, *args):
        """
        Deferred f-string debug logger

        :param fstr: A string to be evaluated as an f-string
        """
        self.__deferred_flog(fstr, logging.DEBUG, *args)

    def finfo(self, fstr, *args):
        """
        Deferred f-string info logger

        :param fstr: A string to be evaluated as an f-string
        """
        self.__deferred_flog(fstr, logging.INFO, *args)

    def __deferred_flog(self, fstr, level, *args):
        if self.isEnabledFor(level):
            import inspect

            frame = inspect.currentframe().f_back.f_back
            try:
                fstr = 'f"' + fstr + '"'
                self.log(
                    level, eval(fstr, frame.f_globals, frame.f_locals), stacklevel=3
                )
            except:
                self.exception("Error converting args to str")
                del frame


def _setup() -> UltestLogger:
    logfile = os.environ.get(
        "ULTEST_LOG_FILE", os.path.join(tempfile.gettempdir(), "vim-ultest.log")
    )
    logger = UltestLogger(name="ultest")
    if logfile:
        handler = logging.FileHandler(logfile, "w", "utf-8")
        handler.formatter = logging.Formatter(
            " | ".join(
                [
                    "%(asctime)s",
                    "%(levelname)s",
                    "%(threadName)s",
                    "%(filename)s:%(funcName)s:%(lineno)s",
                    "%(message)s",
                ]
            ),
            datefmt="%H:%M:%S",
        )
        logger.addHandler(handler)
        level = logging.INFO
        env_log_level = os.environ.get("ULTEST_LOG_LEVEL", None)
        if env_log_level is not None:
            lvl = getattr(logging, env_log_level.strip(), None)
            if isinstance(lvl, int):
                level = lvl
            else:
                logger.warning(
                    "Invalid NVIM_PYTHON_LOG_LEVEL: %r, using INFO.", env_log_level
                )
        logger.setLevel(level)
    return logger


logger: UltestLogger = _setup()
