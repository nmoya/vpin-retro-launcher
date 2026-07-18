import logging
import os
import time
from enum import Enum, auto

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

logger = logging.getLogger(__name__)

L2_AXIS = 4
R2_AXIS = 5
LEFT_ANALOG_Y_AXIS = 1
CIRCLE_BUTTON = 1
L2_BUTTON = 6
R2_BUTTON = 7
SELECT_BUTTON = 8
DPAD_UP_BUTTON = 11
DPAD_DOWN_BUTTON = 12
TRIGGER_PRESS_THRESHOLD = 0.5
TRIGGER_RELEASE_THRESHOLD = 0.25
RESCAN_SECONDS = 1.0


class GamepadEvent(Enum):
    CURSOR_DOWN = auto()
    CURSOR_UP = auto()
    LAUNCH = auto()
    QUIT = auto()


class GamepadController:
    def __init__(self) -> None:
        self.joysticks: dict[int, pygame.joystick.JoystickType] = {}
        self.l2_pressed: dict[int, bool] = {}
        self.r2_pressed: dict[int, bool] = {}
        self.left_analog_up_pressed: dict[int, bool] = {}
        self.left_analog_down_pressed: dict[int, bool] = {}
        self.dpad_hat_up_pressed: dict[int, bool] = {}
        self.dpad_hat_down_pressed: dict[int, bool] = {}
        self.dpad_button_up_pressed: dict[int, bool] = {}
        self.dpad_button_down_pressed: dict[int, bool] = {}
        self.circle_pressed: dict[int, bool] = {}
        self.select_pressed: dict[int, bool] = {}
        self.debug_axes: dict[tuple[int, int], float] = {}
        self.debug_buttons: dict[tuple[int, int], bool] = {}
        self.debug_hats: dict[tuple[int, int], tuple[int, int]] = {}
        self.next_rescan_at = 0.0
        self.started = False

    def start(self) -> None:
        try:
            pygame.display.init()
            pygame.joystick.init()
        except pygame.error as error:
            logger.warning("Unable to initialize gamepad support: %s", error)
            return

        self.started = True
        self.scan_joysticks()

        if not self.joysticks:
            logger.info("No gamepad connected; keyboard controls remain active")

    def stop(self) -> None:
        if not self.started:
            return

        self.joysticks.clear()
        self.l2_pressed.clear()
        self.r2_pressed.clear()
        self.left_analog_up_pressed.clear()
        self.left_analog_down_pressed.clear()
        self.dpad_hat_up_pressed.clear()
        self.dpad_hat_down_pressed.clear()
        self.dpad_button_up_pressed.clear()
        self.dpad_button_down_pressed.clear()
        self.circle_pressed.clear()
        self.select_pressed.clear()
        self.debug_axes.clear()
        self.debug_buttons.clear()
        self.debug_hats.clear()
        pygame.joystick.quit()
        pygame.display.quit()
        self.started = False

    def poll_events(self) -> list[GamepadEvent]:
        if not self.started:
            return []

        try:
            pygame.event.pump()
        except pygame.error as error:
            logger.warning("Unable to poll gamepad events: %s", error)
            return []

        now = time.monotonic()
        if now >= self.next_rescan_at:
            self.scan_joysticks()
            self.next_rescan_at = now + RESCAN_SECONDS

        events = []
        for instance_id, joystick in list(self.joysticks.items()):
            if not self._is_attached(joystick):
                self.remove_joystick(instance_id)
                continue

            self._log_debug_inputs(instance_id, joystick)
            self._poll_dpad(instance_id, joystick, events)
            self._poll_left_analog(instance_id, joystick, events)
            self._poll_triggers(instance_id, joystick, events)
            self._poll_circle(instance_id, joystick, events)
            self._poll_select(instance_id, joystick, events)

        return events

    def scan_joysticks(self) -> None:
        seen_instance_ids = set()
        count = pygame.joystick.get_count()

        for index in range(count):
            try:
                joystick = pygame.joystick.Joystick(index)
                joystick.init()
                instance_id = joystick.get_instance_id()
            except pygame.error as error:
                logger.warning("Unable to initialize gamepad %s: %s", index, error)
                continue

            seen_instance_ids.add(instance_id)
            if instance_id not in self.joysticks:
                self.add_joystick(instance_id, joystick)

        for instance_id in set(self.joysticks) - seen_instance_ids:
            self.remove_joystick(instance_id)

    def add_joystick(self, instance_id: int, joystick: pygame.joystick.JoystickType) -> None:
        self.joysticks[instance_id] = joystick
        self.l2_pressed[instance_id] = False
        self.r2_pressed[instance_id] = False
        self.left_analog_up_pressed[instance_id] = False
        self.left_analog_down_pressed[instance_id] = False
        self.dpad_hat_up_pressed[instance_id] = False
        self.dpad_hat_down_pressed[instance_id] = False
        self.dpad_button_up_pressed[instance_id] = False
        self.dpad_button_down_pressed[instance_id] = False
        self.circle_pressed[instance_id] = False
        self.select_pressed[instance_id] = False
        logger.info(
            "Gamepad connected: %s axes=%s buttons=%s hats=%s",
            joystick.get_name(),
            joystick.get_numaxes(),
            joystick.get_numbuttons(),
            joystick.get_numhats(),
        )

    def remove_joystick(self, instance_id: int) -> None:
        joystick = self.joysticks.pop(instance_id, None)
        self.l2_pressed.pop(instance_id, None)
        self.r2_pressed.pop(instance_id, None)
        self.left_analog_up_pressed.pop(instance_id, None)
        self.left_analog_down_pressed.pop(instance_id, None)
        self.dpad_hat_up_pressed.pop(instance_id, None)
        self.dpad_hat_down_pressed.pop(instance_id, None)
        self.dpad_button_up_pressed.pop(instance_id, None)
        self.dpad_button_down_pressed.pop(instance_id, None)
        self.circle_pressed.pop(instance_id, None)
        self.select_pressed.pop(instance_id, None)
        self._clear_debug_state(instance_id)

        if joystick is not None:
            logger.info("Gamepad disconnected: %s", joystick.get_name())

    def _poll_dpad(
        self,
        instance_id: int,
        joystick: pygame.joystick.JoystickType,
        events: list[GamepadEvent],
    ) -> None:
        hat_value = self._hat_value(joystick, 0)
        if hat_value is not None:
            _, y_value = hat_value
            self.dpad_hat_up_pressed[instance_id] = self._poll_digital(
                y_value > 0,
                self.dpad_hat_up_pressed[instance_id],
                GamepadEvent.CURSOR_UP,
                events,
            )
            self.dpad_hat_down_pressed[instance_id] = self._poll_digital(
                y_value < 0,
                self.dpad_hat_down_pressed[instance_id],
                GamepadEvent.CURSOR_DOWN,
                events,
            )
            return

        up_pressed = self._button_pressed(joystick, DPAD_UP_BUTTON)
        if up_pressed is not None:
            self.dpad_button_up_pressed[instance_id] = self._poll_digital(
                up_pressed,
                self.dpad_button_up_pressed[instance_id],
                GamepadEvent.CURSOR_UP,
                events,
            )

        down_pressed = self._button_pressed(joystick, DPAD_DOWN_BUTTON)
        if down_pressed is not None:
            self.dpad_button_down_pressed[instance_id] = self._poll_digital(
                down_pressed,
                self.dpad_button_down_pressed[instance_id],
                GamepadEvent.CURSOR_DOWN,
                events,
            )

    def _poll_left_analog(
        self,
        instance_id: int,
        joystick: pygame.joystick.JoystickType,
        events: list[GamepadEvent],
    ) -> None:
        y_value = self._axis_value(joystick, LEFT_ANALOG_Y_AXIS)
        if y_value is None:
            return

        self.left_analog_up_pressed[instance_id] = self._poll_negative_axis(
            y_value,
            self.left_analog_up_pressed[instance_id],
            GamepadEvent.CURSOR_UP,
            events,
        )
        self.left_analog_down_pressed[instance_id] = self._poll_positive_axis(
            y_value,
            self.left_analog_down_pressed[instance_id],
            GamepadEvent.CURSOR_DOWN,
            events,
        )

    def _poll_triggers(
        self,
        instance_id: int,
        joystick: pygame.joystick.JoystickType,
        events: list[GamepadEvent],
    ) -> None:
        self.l2_pressed[instance_id] = self._poll_digital(
            self._trigger_pressed(joystick, L2_AXIS, L2_BUTTON),
            self.l2_pressed[instance_id],
            GamepadEvent.CURSOR_DOWN,
            events,
        )
        self.r2_pressed[instance_id] = self._poll_digital(
            self._trigger_pressed(joystick, R2_AXIS, R2_BUTTON),
            self.r2_pressed[instance_id],
            GamepadEvent.CURSOR_UP,
            events,
        )

    def _trigger_pressed(self, joystick: pygame.joystick.JoystickType, axis: int, button: int) -> bool:
        axis_value = self._axis_value(joystick, axis)
        button_pressed = self._button_pressed(joystick, button)
        return (axis_value is not None and axis_value >= TRIGGER_PRESS_THRESHOLD) or bool(button_pressed)

    def _poll_positive_axis(
        self,
        value: float,
        pressed: bool,
        event: GamepadEvent,
        events: list[GamepadEvent],
    ) -> bool:
        if not pressed and value >= TRIGGER_PRESS_THRESHOLD:
            events.append(event)
            return True

        if pressed and value <= TRIGGER_RELEASE_THRESHOLD:
            return False

        return pressed

    def _poll_negative_axis(
        self,
        value: float,
        pressed: bool,
        event: GamepadEvent,
        events: list[GamepadEvent],
    ) -> bool:
        if not pressed and value <= -TRIGGER_PRESS_THRESHOLD:
            events.append(event)
            return True

        if pressed and value >= -TRIGGER_RELEASE_THRESHOLD:
            return False

        return pressed

    def _poll_digital(
        self,
        is_pressed: bool,
        was_pressed: bool,
        event: GamepadEvent,
        events: list[GamepadEvent],
    ) -> bool:
        if is_pressed and not was_pressed:
            events.append(event)

        return is_pressed

    def _poll_circle(
        self,
        instance_id: int,
        joystick: pygame.joystick.JoystickType,
        events: list[GamepadEvent],
    ) -> None:
        is_pressed = self._button_pressed(joystick, CIRCLE_BUTTON)
        if is_pressed is None:
            return

        self.circle_pressed[instance_id] = self._poll_digital(
            is_pressed,
            self.circle_pressed[instance_id],
            GamepadEvent.LAUNCH,
            events,
        )

    def _poll_select(
        self,
        instance_id: int,
        joystick: pygame.joystick.JoystickType,
        events: list[GamepadEvent],
    ) -> None:
        is_pressed = self._button_pressed(joystick, SELECT_BUTTON)
        if is_pressed is None:
            return

        self.select_pressed[instance_id] = self._poll_digital(
            is_pressed,
            self.select_pressed[instance_id],
            GamepadEvent.QUIT,
            events,
        )

    def _log_debug_inputs(self, instance_id: int, joystick: pygame.joystick.JoystickType) -> None:
        if not logger.isEnabledFor(logging.DEBUG):
            return

        for axis in range(joystick.get_numaxes()):
            value = self._axis_value(joystick, axis)
            if value is None:
                continue

            key = (instance_id, axis)
            previous_value = self.debug_axes.get(key)
            if previous_value is None or abs(value - previous_value) >= 0.1:
                logger.debug(
                    "Gamepad axis changed: name=%s axis=%s value=%.3f",
                    joystick.get_name(),
                    axis,
                    value,
                )
                self.debug_axes[key] = value

        for button in range(joystick.get_numbuttons()):
            is_pressed = self._button_pressed(joystick, button)
            if is_pressed is None:
                continue

            key = (instance_id, button)
            previous_pressed = self.debug_buttons.get(key)
            if previous_pressed is None or is_pressed != previous_pressed:
                logger.debug(
                    "Gamepad button changed: name=%s button=%s pressed=%s",
                    joystick.get_name(),
                    button,
                    is_pressed,
                )
                self.debug_buttons[key] = is_pressed

        for hat in range(joystick.get_numhats()):
            value = self._hat_value(joystick, hat)
            if value is None:
                continue

            key = (instance_id, hat)
            previous_value = self.debug_hats.get(key)
            if previous_value is None or value != previous_value:
                logger.debug(
                    "Gamepad hat changed: name=%s hat=%s value=%s",
                    joystick.get_name(),
                    hat,
                    value,
                )
                self.debug_hats[key] = value

    def _axis_value(self, joystick: pygame.joystick.JoystickType, axis: int) -> float | None:
        if axis >= joystick.get_numaxes():
            return None

        try:
            return joystick.get_axis(axis)
        except pygame.error as error:
            logger.warning("Unable to read gamepad axis %s: %s", axis, error)
            return None

    def _button_pressed(self, joystick: pygame.joystick.JoystickType, button: int) -> bool | None:
        if button >= joystick.get_numbuttons():
            return None

        try:
            return bool(joystick.get_button(button))
        except pygame.error as error:
            logger.warning("Unable to read gamepad button %s: %s", button, error)
            return None

    def _hat_value(self, joystick: pygame.joystick.JoystickType, hat: int) -> tuple[int, int] | None:
        if hat >= joystick.get_numhats():
            return None

        try:
            return joystick.get_hat(hat)
        except pygame.error as error:
            logger.warning("Unable to read gamepad hat %s: %s", hat, error)
            return None

    def _is_attached(self, joystick: pygame.joystick.JoystickType) -> bool:
        get_attached = getattr(joystick, "get_attached", None)
        if get_attached is None:
            return True

        try:
            return bool(get_attached())
        except pygame.error:
            return False

    def _clear_debug_state(self, instance_id: int) -> None:
        for key in list(self.debug_axes):
            if key[0] == instance_id:
                self.debug_axes.pop(key)

        for key in list(self.debug_buttons):
            if key[0] == instance_id:
                self.debug_buttons.pop(key)

        for key in list(self.debug_hats):
            if key[0] == instance_id:
                self.debug_hats.pop(key)
