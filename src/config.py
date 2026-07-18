import json
import os


class Config:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self.load_config()
        self._orientation = self.data.get("orientation", "horizontal")
        self._vpxtool_path = self.data.get("vpxtool_path", "")
        self._vpinball_path = self.data.get("vpinball_path", "")
        self._chafa_path = self.data.get("chafa_path", "")
        self._tables_root = self.data.get("tables_root", "")
        self._cover_art_width = self.data.get("cover_art_width", 72)

    def load_config(self):
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def is_valid(self):
        try:
            self.orientation
            self.vpxtool_path
            self.vpinball_path
            self.chafa_path
            self.tables_root
            self.cover_art_width
        except ValueError:
            return False

        return True

    @property
    def orientation(self):
        if self._orientation not in ["horizontal", "vertical"]:
            raise ValueError("Invalid orientation. Must be 'horizontal' or 'vertical'.")

        return self._orientation

    @property
    def vpxtool_path(self):
        if not os.path.isfile(self._vpxtool_path):
            raise ValueError("Invalid vpxtool path. Must be a valid file path.")

        return self._vpxtool_path

    @property
    def vpinball_path(self):
        if not os.path.isfile(self._vpinball_path):
            raise ValueError("Invalid vpinball path. Must be a valid file path.")

        return self._vpinball_path

    @property
    def chafa_path(self):
        if not os.path.isfile(self._chafa_path):
            raise ValueError("Invalid chafa path. Must be a valid file path.")

        return self._chafa_path

    @property
    def tables_root(self):
        if not os.path.isdir(self._tables_root):
            raise ValueError("Invalid tables root. Must be a valid directory path.")

        return self._tables_root

    @property
    def cover_art_width(self):
        try:
            width = int(self._cover_art_width)
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid cover art width. Must be a positive integer.") from error

        if width <= 0:
            raise ValueError("Invalid cover art width. Must be a positive integer.")

        return width
