import logging
import os
import tempfile
from logging import handlers


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

    def makeRecord(
        self,
        name,
        level,
        fn,
        lno,
        msg,
        args,
        exc_info,
        func=None,
        extra=None,
        sinfo=None,
    ):
        rv = logging.getLogRecordFactory()(
            name, level, fn, lno, msg, args, exc_info, func, sinfo
        )
        if extra is not None:
            for key in extra:
                rv.__dict__[key] = extra[key]
        return rv

    def __deferred_flog(self, fstr, level, *args):
        if self.isEnabledFor(level):
            try:
                import inspect

                frame = inspect.currentframe().f_back.f_back
                code = frame.f_code
                extra = {
                    "filename": os.path.split(code.co_filename)[-1],
                    "funcName": code.co_name,
                    "lineno": frame.f_lineno,
                }
                fstr = 'f"' + fstr + '"'
                self.log(
                    level, eval(fstr, frame.f_globals, frame.f_locals), extra=extra
                )
            except Exception as e:
                self.error(f"Error {e} converting args to str {fstr}")


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


_logger = None


def get_logger() -> UltestLogger:
    global _logger
    if not _logger:
        _logger = create_logger()
    return _logger
