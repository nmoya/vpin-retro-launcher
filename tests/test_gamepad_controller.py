from gamepad_controller import GamepadController


class FakeJoystick:
    def __init__(self, axes=None, buttons=None, hats=None, attached=True, has_get_attached=True):
        self.axes = axes or {}
        self.buttons = buttons or {}
        self.hats = hats or {}
        self.attached = attached
        self.has_get_attached = has_get_attached

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
        if not self.has_get_attached:
            raise AttributeError
        return self.attached


def controller_with_actions():
    actions = []
    controller = GamepadController(
        cursor_down=lambda: actions.append("down"),
        cursor_up=lambda: actions.append("up"),
        launch=lambda: actions.append("launch"),
    )
    controller.add_joystick(0, FakeJoystick())
    return controller, actions


def test_l2_axis_and_button_trigger_down_once_until_released():
    controller, actions = controller_with_actions()

    controller._poll_triggers(0, FakeJoystick(axes={4: 0.6}))
    controller._poll_triggers(0, FakeJoystick(axes={4: 0.8}))
    controller._poll_triggers(0, FakeJoystick(axes={4: 0.0}))
    controller._poll_triggers(0, FakeJoystick(buttons={6: True}))

    assert actions == ["down", "down"]


def test_r2_axis_and_button_trigger_up():
    controller, actions = controller_with_actions()

    controller._poll_triggers(0, FakeJoystick(axes={5: 0.6}))
    controller._poll_triggers(0, FakeJoystick(axes={5: 0.0}))
    controller._poll_triggers(0, FakeJoystick(buttons={7: True}))

    assert actions == ["up", "up"]


def test_circle_button_launches_once_per_press():
    controller, actions = controller_with_actions()

    controller._poll_circle(0, FakeJoystick(buttons={1: True}))
    controller._poll_circle(0, FakeJoystick(buttons={1: True}))
    controller._poll_circle(0, FakeJoystick(buttons={1: False}))
    controller._poll_circle(0, FakeJoystick(buttons={1: True}))

    assert actions == ["launch", "launch"]


def test_dpad_hat_up_and_down_trigger_navigation():
    controller, actions = controller_with_actions()

    controller._poll_dpad(0, FakeJoystick(hats={0: (0, 1)}))
    controller._poll_dpad(0, FakeJoystick(hats={0: (0, 0)}))
    controller._poll_dpad(0, FakeJoystick(hats={0: (0, -1)}))

    assert actions == ["up", "down"]


def test_dpad_button_fallback_triggers_navigation():
    controller, actions = controller_with_actions()

    controller._poll_dpad(0, FakeJoystick(buttons={11: True}))
    controller._poll_dpad(0, FakeJoystick(buttons={11: False}))
    controller._poll_dpad(0, FakeJoystick(buttons={12: True}))

    assert actions == ["up", "down"]


def test_left_analog_up_and_down_trigger_navigation_with_debounce():
    controller, actions = controller_with_actions()

    controller._poll_left_analog(0, FakeJoystick(axes={1: -0.6}))
    controller._poll_left_analog(0, FakeJoystick(axes={1: -0.8}))
    controller._poll_left_analog(0, FakeJoystick(axes={1: 0.0}))
    controller._poll_left_analog(0, FakeJoystick(axes={1: 0.6}))

    assert actions == ["up", "down"]


def test_is_attached_handles_joystick_without_get_attached():
    controller, _ = controller_with_actions()

    class NoGetAttached:
        pass

    assert controller._is_attached(NoGetAttached()) is True
