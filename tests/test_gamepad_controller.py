from gamepad_controller import GamepadController, GamepadEvent


class FakeJoystick:
    def __init__(self, axes=None, buttons=None, hats=None, attached=True):
        self.axes = axes or {}
        self.buttons = buttons or {}
        self.hats = hats or {}
        self.attached = attached

    def get_name(self):
        return "Fake Controller"

    def get_numaxes(self):
        return max(self.axes.keys(), default=-1) + 1

    def get_axis(self, axis):
        return self.axes.get(axis, 0.0)

    def get_numbuttons(self):
        return max(self.buttons.keys(), default=-1) + 1

    def get_button(self, button):
        return int(self.buttons.get(button, False))

    def get_numhats(self):
        return max(self.hats.keys(), default=-1) + 1

    def get_hat(self, hat):
        return self.hats.get(hat, (0, 0))

    def get_attached(self):
        return self.attached


def controller_with_events():
    controller = GamepadController()
    controller.add_joystick(0, FakeJoystick())
    return controller, []


def test_l2_axis_and_button_emit_down_once_until_released():
    controller, events = controller_with_events()

    controller._poll_triggers(0, FakeJoystick(axes={4: 0.6}), events)
    controller._poll_triggers(0, FakeJoystick(axes={4: 0.8}), events)
    controller._poll_triggers(0, FakeJoystick(axes={4: 0.0}), events)
    controller._poll_triggers(0, FakeJoystick(buttons={6: True}), events)

    assert events == [GamepadEvent.CURSOR_DOWN, GamepadEvent.CURSOR_DOWN]


def test_r2_axis_and_button_emit_up():
    controller, events = controller_with_events()

    controller._poll_triggers(0, FakeJoystick(axes={5: 0.6}), events)
    controller._poll_triggers(0, FakeJoystick(axes={5: 0.0}), events)
    controller._poll_triggers(0, FakeJoystick(buttons={7: True}), events)

    assert events == [GamepadEvent.CURSOR_UP, GamepadEvent.CURSOR_UP]


def test_circle_button_emits_launch_once_per_press():
    controller, events = controller_with_events()

    controller._poll_circle(0, FakeJoystick(buttons={1: True}), events)
    controller._poll_circle(0, FakeJoystick(buttons={1: True}), events)
    controller._poll_circle(0, FakeJoystick(buttons={1: False}), events)
    controller._poll_circle(0, FakeJoystick(buttons={1: True}), events)

    assert events == [GamepadEvent.LAUNCH, GamepadEvent.LAUNCH]


def test_select_button_emits_quit_once_per_press():
    controller, events = controller_with_events()

    controller._poll_select(0, FakeJoystick(buttons={8: True}), events)
    controller._poll_select(0, FakeJoystick(buttons={8: True}), events)
    controller._poll_select(0, FakeJoystick(buttons={8: False}), events)
    controller._poll_select(0, FakeJoystick(buttons={8: True}), events)

    assert events == [GamepadEvent.QUIT, GamepadEvent.QUIT]


def test_dpad_hat_up_and_down_emit_navigation():
    controller, events = controller_with_events()

    controller._poll_dpad(0, FakeJoystick(hats={0: (0, 1)}), events)
    controller._poll_dpad(0, FakeJoystick(hats={0: (0, 0)}), events)
    controller._poll_dpad(0, FakeJoystick(hats={0: (0, -1)}), events)

    assert events == [GamepadEvent.CURSOR_UP, GamepadEvent.CURSOR_DOWN]


def test_dpad_button_fallback_emits_navigation():
    controller, events = controller_with_events()

    controller._poll_dpad(0, FakeJoystick(buttons={11: True}), events)
    controller._poll_dpad(0, FakeJoystick(buttons={11: False}), events)
    controller._poll_dpad(0, FakeJoystick(buttons={12: True}), events)

    assert events == [GamepadEvent.CURSOR_UP, GamepadEvent.CURSOR_DOWN]


def test_left_analog_up_and_down_emit_navigation_with_debounce():
    controller, events = controller_with_events()

    controller._poll_left_analog(0, FakeJoystick(axes={1: -0.6}), events)
    controller._poll_left_analog(0, FakeJoystick(axes={1: -0.8}), events)
    controller._poll_left_analog(0, FakeJoystick(axes={1: 0.0}), events)
    controller._poll_left_analog(0, FakeJoystick(axes={1: 0.6}), events)

    assert events == [GamepadEvent.CURSOR_UP, GamepadEvent.CURSOR_DOWN]


def test_poll_events_returns_empty_when_not_started():
    assert GamepadController().poll_events() == []


def test_is_attached_handles_joystick_without_get_attached():
    controller, _ = controller_with_events()

    class NoGetAttached:
        pass

    assert controller._is_attached(NoGetAttached()) is True
