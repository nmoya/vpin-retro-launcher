from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import os

from data import TableScore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HighScoreRecord:
    name: str
    initials: str
    score: str
    first_seen_at: str | None

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> "HighScoreRecord":
        return cls(
            name=data.get("name", ""),
            initials=data.get("initials", ""),
            score=data.get("score", ""),
            first_seen_at=data.get("first_seen_at", None),
        )

    def to_dict(self) -> dict[str, str | None]:
        return {
            "name": self.name,
            "initials": self.initials,
            "score": self.score,
            "first_seen_at": self.first_seen_at,
        }

    def identity(self) -> tuple[str, str, str]:
        return (self.name, self.initials, self.score)


@dataclass
class TableStats:
    table_name: str = ""
    last_played_at: str = ""
    launches_count: int = 0
    total_play_time_seconds: int = 0
    high_scores: list[HighScoreRecord] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "TableStats":
        high_scores = data.get("high_scores", [])
        return cls(
            table_name=data.get("table_name", ""),
            last_played_at=str(data.get("last_played_at", "")),
            launches_count=int(data.get("launches_count", 0)),
            total_play_time_seconds=int(data.get("total_play_time_seconds", 0)),
            high_scores=[HighScoreRecord.from_dict(score) for score in high_scores if isinstance(score, dict)],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "table_name": self.table_name,
            "last_played_at": self.last_played_at,
            "launches_count": self.launches_count,
            "total_play_time_seconds": self.total_play_time_seconds,
            "high_scores": [score.to_dict() for score in self.high_scores],
        }


@dataclass
class VPinData:
    tables: dict[str, TableStats] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "VPinData":
        tables = data.get("tables", {})
        if not isinstance(tables, dict):
            return cls()

        return cls(
            tables={
                table_md5: TableStats.from_dict(stats)
                for table_md5, stats in tables.items()
                if isinstance(table_md5, str) and isinstance(stats, dict)
            }
        )

    def to_dict(self) -> dict[str, object]:
        return {"tables": {table_md5: stats.to_dict() for table_md5, stats in self.tables.items()}}


class VPinDataStore:
    def __init__(self, filepath: str = "vpin_data.json") -> None:
        self.filepath = filepath
        self.data = self.load()

    def load(self) -> VPinData:
        try:
            with open(self.filepath, "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            return VPinData()
        except json.JSONDecodeError as error:
            logger.warning("Ignoring invalid vpin data file %s: %s", self.filepath, error)
            return VPinData()

        if not isinstance(data, dict):
            return VPinData()

        return VPinData.from_dict(data)

    def save(self) -> None:
        temp_filepath = f"{self.filepath}.tmp"
        with open(temp_filepath, "w") as file:
            json.dump(self.data.to_dict(), file, indent=2)
            file.write("\n")

        os.replace(temp_filepath, self.filepath)

    def table_stats(self, table_md5: str) -> TableStats:
        if table_md5 not in self.data.tables:
            self.data.tables[table_md5] = TableStats()
        return self.data.tables[table_md5]

    def import_table(self, table_md5: str, table_name: str, scores: list[TableScore]) -> None:
        self.update_high_scores(table_md5, table_name, scores, imported=True)

    def record_launch(self, table_md5: str, table_name: str, timestamp: str | None = None) -> None:
        stats = self.table_stats(table_md5)
        stats.table_name = table_name
        stats.launches_count += 1
        stats.last_played_at = timestamp or utc_now()
        self.save()

    def record_play_time(self, table_md5: str, play_seconds: int) -> None:
        stats = self.table_stats(table_md5)
        stats.total_play_time_seconds += max(play_seconds, 0)
        self.save()

    def update_high_scores(
        self,
        table_md5: str,
        table_name: str,
        scores: list[TableScore],
        timestamp: str | None = None,
        imported: bool = False,
    ) -> None:
        stats = self.table_stats(table_md5)
        stats.table_name = table_name
        first_seen_at = None if imported else timestamp or utc_now()
        existing_scores = {score.identity(): score.first_seen_at for score in stats.high_scores}

        stats.high_scores = [
            HighScoreRecord(
                name=score.name,
                initials=score.initials,
                score=score.score,
                first_seen_at=existing_scores.get((score.name, score.initials, score.score), first_seen_at),
            )
            for score in scores
        ]
        self.save()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
