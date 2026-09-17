"""Load and validate the immutable source-data JSON files."""

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.models.source_data import (
    CalendarData,
    EmailsData,
    MeetingsData,
    PeopleData,
    SourceData,
    VoiceNotesData,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


class DataLoadError(RuntimeError):
    """Raised when a source-data file is missing, invalid JSON, or malformed."""


class SourceDataLoader:
    """Repository for raw assignment data stored as validated JSON files."""

    def __init__(self, data_dir: Path | str | None = None) -> None:
        project_root = Path(__file__).resolve().parents[3]
        self.data_dir = Path(data_dir) if data_dir is not None else project_root / "data"

    def load_all(self) -> SourceData:
        """Load every source file and return clean Pydantic objects."""
        return SourceData(
            people=self.load_people(),
            emails=self.load_emails(),
            calendar=self.load_calendar(),
            meetings=self.load_meetings(),
            voice_notes=self.load_voice_notes(),
        )

    def load_people(self) -> PeopleData:
        return self._load("people.json", PeopleData)

    def load_emails(self) -> EmailsData:
        return self._load("emails.json", EmailsData)

    def load_calendar(self) -> CalendarData:
        return self._load("calendar.json", CalendarData)

    def load_meetings(self) -> MeetingsData:
        return self._load("meetings.json", MeetingsData)

    def load_voice_notes(self) -> VoiceNotesData:
        return self._load("voice_notes.json", VoiceNotesData)

    def _load(self, filename: str, model_type: type[ModelT]) -> ModelT:
        path = self.data_dir / filename
        try:
            raw_data: Any = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise DataLoadError(f"Source data file is missing: {path}") from exc
        except UnicodeDecodeError as exc:
            raise DataLoadError(f"Source data file is not UTF-8: {path}") from exc
        except json.JSONDecodeError as exc:
            raise DataLoadError(
                f"Source data file contains invalid JSON: {path} (line {exc.lineno}, column {exc.colno})"
            ) from exc

        try:
            return model_type.model_validate(raw_data)
        except ValidationError as exc:
            raise DataLoadError(f"Source data file has an invalid structure: {path}: {exc}") from exc
