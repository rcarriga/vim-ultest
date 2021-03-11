import logging
import os
import tempfile
from logging import handlers

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


def create_logger() -> UltestLogger:
    logfile = os.environ.get(
        "ULTEST_LOG_FILE", os.path.join(tempfile.gettempdir(), "vim-ultest.log")
    )
    logger = UltestLogger(name="ultest")
    if logfile:
        env_level = os.environ.get("ULTEST_LOG_LEVEL", "INFO")
        level = getattr(logging, env_level.strip(), None)
        format = [
            "%(asctime)s",
            "%(levelname)s",
            "%(threadName)s",
            "%(filename)s:%(funcName)s:%(lineno)s",
            "%(message)s",
        ]
        if not isinstance(level, int):
            logger.warning("Invalid NVIM_PYTHON_LOG_LEVEL: %r, using INFO.", env_level)
            level = logging.INFO
        if level >= logging.INFO:
            logging.logThreads = 0
            logging.logProcesses = 0
            logging._srcfile = None
            format.pop(-3)
            format.pop(-2)
        handler = handlers.RotatingFileHandler(
            logfile, maxBytes=20 * 1024, backupCount=1
        )
        handler.formatter = logging.Formatter(
            " | ".join(format),
            datefmt="%H:%M:%S",
        )
        logger.addHandler(handler)
        logger.setLevel(level)
    logger.info("Logger created")
    return logger
