from dataclasses import dataclass


@dataclass(frozen=True)
class TableInfo:
    name: str
    vpx_version: str
    version: str
    published_date: str
    revision: str
    description: str
    path: str

    def __repr__(self) -> str:
        return "\n".join(
            [
                f"Name: {self.name}",
                f"VPX Version: {self.vpx_version}",
                f"Table Version: {self.version}",
                f"Published Date: {self.published_date}",
                f"Revision: {self.revision}",
                f"Description: {self.description}",
                f"Path: {self.path}",
            ]
        )


@dataclass(frozen=True)
class TableScore:
    name: str
    initials: str
    score: str

    def __repr__(self) -> str:
        return f"{self.name} ({self.initials}): {self.score}"


@dataclass(frozen=True)
class TableItem:
    info: TableInfo
    scores: list[TableScore]
    md5: str
