from data import TableInfo, TableScore
import json
import subprocess
import os


class VPXToolBridge:
    def __init__(self, vpxtool_path: str):
        self.vpxtool_path = vpxtool_path

    def execute(self, args: list[str]) -> str:
        command = [self.vpxtool_path] + args
        result = subprocess.check_output(command, text=True, stderr=subprocess.PIPE)
        return result

    def _parse_info_output(self, table_path: str, info_path: str) -> TableInfo:
        with open(info_path, "r") as f:
            data = json.load(f)
        return TableInfo(
            name=data.get("table_name", ""),
            vpx_version=data.get("vpx_version", ""),
            version=data.get("table_version", ""),
            published_date=data.get("table_save_date", ""),
            description=data.get("table_description", ""),
            revision=data.get("table_save_rev", ""),
            path=table_path,
        )

    def info(self, table_path: str) -> TableInfo:
        extract_output = table_path.replace(".vpx", ".info.json")
        if os.path.exists(extract_output):
            os.remove(extract_output)
        _ = self.execute(["info", "extract", table_path])
        info_data = self._parse_info_output(table_path, extract_output)
        if os.path.exists(extract_output):
            os.remove(extract_output)
        return info_data

    def scores(self, table_path: str) -> list[TableScore]:
        try:
            output = self.execute(["scores", "show", table_path])
        except subprocess.CalledProcessError:
            return []

        lines = output.strip().splitlines()
        scores = []
        for line in lines[1:]:  # Skip the first line (header)
            parts = line.split("  ")
            non_empty_parts = [part.strip() for part in parts if part.strip()]
            if len(non_empty_parts) < 3:
                continue
            scores.append(TableScore(name=non_empty_parts[0], initials=non_empty_parts[1], score=non_empty_parts[2]))
        return scores


if __name__ == "__main__":
    vpxtool_path = "/etc/profiles/per-user/nmoya/bin/vpxtool"
    table_path = "/home/nmoya/VPinball/lotr/Lord of the Rings - Stern 2003-1.6.vpx"
    bridge = VPXToolBridge(vpxtool_path)
    table_info = bridge.info(table_path)
    table_scores = bridge.scores(table_path)
    print(f"Table Info: {table_info}")
    for score in table_scores:
        print(score)
