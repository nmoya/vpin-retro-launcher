import subprocess

from gamepad_controller import GamepadEvent
import vpinball_runner
from vpinball_runner import VPinballRunner


class FakeProcess:
    def __init__(self, poll_results):
        self.pid = 1234
        self.poll_results = list(poll_results)
        self.returncode = None
        self.wait_calls = []

    def poll(self):
        result = self.poll_results.pop(0)
        if result is not None:
            self.returncode = result
        return result

    def wait(self, timeout=None):
        self.wait_calls.append(timeout)
        self.returncode = -15
        return self.returncode


def test_runner_waits_for_vpinball_to_exit(monkeypatch):
    process = FakeProcess([None, 0])
    commands = []

    def fake_popen(command, start_new_session):
        commands.append((command, start_new_session))
        return process

    monkeypatch.setattr(vpinball_runner.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(vpinball_runner.time, "sleep", lambda seconds: None)

    returncode = VPinballRunner("vpinball", lambda: []).run("table.vpx")

    assert returncode == 0
    assert commands == [(["vpinball", "table.vpx"], True)]


def test_runner_terminates_process_group_on_quit_event(monkeypatch):
    process = FakeProcess([None])
    signals = []

    monkeypatch.setattr(vpinball_runner.subprocess, "Popen", lambda command, start_new_session: process)
    monkeypatch.setattr(vpinball_runner.os, "killpg", lambda pid, signal: signals.append((pid, signal)))

    returncode = VPinballRunner("vpinball", lambda: [GamepadEvent.QUIT]).run("table.vpx")

    assert returncode == -15
    assert signals == [(1234, vpinball_runner.signal.SIGTERM)]
    assert process.wait_calls == [5.0]


def test_runner_force_kills_if_process_ignores_sigterm(monkeypatch):
    class StubbornProcess(FakeProcess):
        def wait(self, timeout=None):
            self.wait_calls.append(timeout)
            if timeout is not None:
                raise subprocess.TimeoutExpired("vpinball", timeout)
            self.returncode = -9
            return self.returncode

    process = StubbornProcess([None])
    signals = []

    monkeypatch.setattr(vpinball_runner.subprocess, "Popen", lambda command, start_new_session: process)
    monkeypatch.setattr(vpinball_runner.os, "killpg", lambda pid, signal: signals.append((pid, signal)))

    VPinballRunner("vpinball", lambda: [GamepadEvent.QUIT]).run("table.vpx")

    assert signals == [
        (1234, vpinball_runner.signal.SIGTERM),
        (1234, vpinball_runner.signal.SIGKILL),
    ]
    assert process.returncode == -9
