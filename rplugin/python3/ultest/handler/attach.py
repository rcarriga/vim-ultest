import subprocess
import sys

IN_FILE = "{test_process.in_path}"
OUT_FILE = "{test_process.out_path}"


def run():
    devnull = open("/dev/null", "a")
    to_input = open(IN_FILE, "wb")

    subprocess.Popen(
        ["tail", "-F", "-c", "+0", OUT_FILE],
        stdin=devnull,
        stdout=sys.stdout,
        stderr=subprocess.STDOUT,
    )

    try:
        while True:
            in_ = input() + "\n"
            to_input.write(in_.encode())
            to_input.flush()
    except BaseException:
        pass


if __name__ == "__main__":
    run()
