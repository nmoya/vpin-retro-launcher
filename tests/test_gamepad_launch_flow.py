from main import VPinRetroLauncher


class FakeLauncher:
    def __init__(self):
        self.launch_calls = 0

    def launch_selected_table(self):
        self.launch_calls += 1


def test_gamepad_launch_calls_horizontal_launcher_directly():
    app = object.__new__(VPinRetroLauncher)
    launcher = FakeLauncher()
    app.query_one = lambda widget_type: launcher

    app._gamepad_launch()

    assert launcher.launch_calls == 1
