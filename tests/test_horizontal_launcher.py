from layout.horizontal_launcher import HorizontalLauncher


def test_launch_table_ignores_request_while_launch_in_progress():
    launcher = object.__new__(HorizontalLauncher)
    launcher.launch_in_progress = True
    launcher.last_launch_finished_at = 0.0
    calls = []
    launcher._launch_table = lambda list_item: calls.append(list_item)

    launcher.launch_table(object())

    assert calls == []
