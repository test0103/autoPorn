from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Tag:
    id: str
    name: str


@dataclass(slots=True)
class Movie:
    id: str
    name: str
    img_x: str = ""
    img_y: str = ""
    cat_name: str = ""
    is_add: bool = False
    tags: list[Tag] = field(default_factory=list)

    @classmethod
    def from_api(cls, payload: dict) -> "Movie":
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            img_x=str(payload.get("img_x", "")),
            img_y=str(payload.get("img_y", "")),
            cat_name=str(payload.get("cat_name", "")),
            is_add=bool(payload.get("isAdd", False)),
            tags=[Tag(id=str(t.get("id", "")), name=str(t.get("name", ""))) for t in payload.get("tags", [])],
        )

    @property
    def tag_names(self) -> list[str]:
        return [tag.name for tag in self.tags]


@dataclass(slots=True)
class Section:
    id: str
    name: str
    module_name: str
    sub_module_name: str
    tags: list[str] = field(default_factory=list)

    @classmethod
    def flatten_from_api(cls, payload: list[dict]) -> list["Section"]:
        sections: list[Section] = []
        for module in payload:
            for section in module.get("sections", []) or []:
                sections.append(
                    cls(
                        id=str(section.get("id", "")),
                        name=str(section.get("sectionName", "")),
                        module_name=str(module.get("moduleName", "")),
                        sub_module_name=str(module.get("subModuleName", "")),
                        tags=[str(t) for t in (section.get("tags") or [])],
                    )
                )
        return sections
