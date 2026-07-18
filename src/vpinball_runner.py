from collections.abc import Callable
import logging
import os
import signal
import subprocess
import time

from gamepad_controller import GamepadEvent

logger = logging.getLogger(__name__)


class VPinballRunner:
    def __init__(
        self,
        vpinball_path: str,
        poll_gamepad_events: Callable[[], list[GamepadEvent]],
        poll_interval_seconds: float = 0.05,
        terminate_timeout_seconds: float = 5.0,
    ) -> None:
        self.vpinball_path = vpinball_path
        self.poll_gamepad_events = poll_gamepad_events
        self.poll_interval_seconds = poll_interval_seconds
        self.terminate_timeout_seconds = terminate_timeout_seconds

    def run(self, table_path: str) -> int | None:
        process = subprocess.Popen([self.vpinball_path, table_path], start_new_session=True)

        while process.poll() is None:
            if GamepadEvent.QUIT in self.poll_gamepad_events():
                logger.info("Controller quit requested; terminating vpinball")
                self._terminate(process)
                break

            time.sleep(self.poll_interval_seconds)

        return process.returncode

    def _terminate(self, process: subprocess.Popen[bytes]) -> None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return

        try:
            process.wait(timeout=self.terminate_timeout_seconds)
        except subprocess.TimeoutExpired:
            logger.warning("vpinball did not exit after SIGTERM; sending SIGKILL")
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                return
            process.wait()
