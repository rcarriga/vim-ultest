import errno
import os
import readline  # type: ignore
import select
import sys
import time
from threading import Thread

IN_FILE = "{IN_FILE}"
OUT_FILE = "{OUT_FILE}"


def forward_fd(from_fd: int, to_fd: int) -> Thread:
    def forward():
        try:
            while True:
                ready, _, _ = select.select([from_fd], [], [])
                for fd in ready:
                    try:
                        data = os.read(fd, 512)
                        if not data:  # EOF
                            time.sleep(0.1)
                            break
                        os.write(to_fd, data)
                    except OSError as e:
                        if e.errno != errno.EIO:
                            raise
                        # EIO means EOF on some systems
                        break
        except:
            ...

    thread = Thread(target=forward, daemon=True)
    thread.start()
    return thread


def run():
    output_thread = forward_fd(os.open(OUT_FILE, os.O_RDONLY), sys.stdout.fileno())

    # Use a non visible prompt to prevent readline overwriting text from stdout
    # on the last line, where stdin is also written. This is still not perfect,
    # for example vi bindings still allow deleting prompt text.
    try:
        if IN_FILE:
            PROMPT = "\010"

            to_input = os.open(IN_FILE, os.O_WRONLY)
            try:
                while True:
                    in_ = input(PROMPT) + "\n"
                    os.write(to_input, in_.encode())
            except BaseException:
                pass

        else:
            output_thread.join()
    except:
        ...


if __name__ == "__main__":
    run()
