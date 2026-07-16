import json
import os


class Config:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self.load_config()
        self._orientation = self.data.get("orientation", "horizontal")
        self._vpxtool_path = self.data.get("vpxtool_path", "")
        self._tables_root = self.data.get("tables_root", "")

    def load_config(self):
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def is_valid(self):
        return (
            self.orientation in ["horizontal", "vertical"]
            and os.path.isfile(self.vpxtool_path)
            and os.path.isdir(self.tables_root)
        )

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, value: str):
        if value in ["horizontal", "vertical"]:
            self._orientation = value
        else:
            raise ValueError("Invalid orientation. Must be 'horizontal' or 'vertical'.")

    @property
    def vpxtool_path(self):
        return self._vpxtool_path

    @vpxtool_path.setter
    def vpxtool_path(self, value: str):
        if os.path.isfile(value):
            self._vpxtool_path = value
        else:
            raise ValueError("Invalid vpxtool path. Must be a valid file path.")

    @property
    def tables_root(self):
        return self._tables_root

    @tables_root.setter
    def tables_root(self, value: str):
        if os.path.isdir(value):
            self._tables_root = value
        else:
            raise ValueError("Invalid tables root. Must be a valid directory path.")
