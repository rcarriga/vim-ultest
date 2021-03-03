import readline  # type: ignore
import subprocess

IN_FILE = "{test_process.in_path}"
OUT_FILE = "{test_process.out_path}"

# Use a non visible prompt to prevent readline overwriting text from stdout
# on the last line, where stdin is also written. This is still not perfect,
# for example vi bindings still allow deleting prompt text.
PROMPT = "\010"


def run():
    to_input = open(IN_FILE, "wb")

    subprocess.Popen(
        ["tail", "-F", "-c", "+0", OUT_FILE],
        stdin=subprocess.DEVNULL,
        stdout=None,
        stderr=subprocess.STDOUT,
    )

    try:
        while True:
            in_ = input(PROMPT) + "\n"
            to_input.write(in_.encode())
            to_input.flush()
    except BaseException:
        pass


if __name__ == "__main__":
    run()
