"""Starts apps detached from the shell, so closing or crashing the shell does not close them."""
import subprocess

from ..domain import desktop_entry

_TERMINAL = ["foot"]


def launch(entry):
    command = desktop_entry.argv(entry)
    if entry.terminal:
        command = _TERMINAL + ["-e"] + command
    subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
