from __future__ import annotations

import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

_MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}

_SINGLE_DATE_PATTERN = re.compile(
    r"(?P<day>\d{1,2})\s+(?P<month>января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(?P<year>\d{4})",
    re.IGNORECASE,
)

_RANGE_DATE_PATTERN = re.compile(
    r"с\s+(?P<start_day>\d{1,2})\s+по\s+(?P<end_day>\d{1,2})\s+(?P<month>января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(?P<year>\d{4})",
    re.IGNORECASE,
)


class DateRange(BaseModel):
    start_date: date
    end_date: date


class DBQuestion(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    normalized_question: str | None = None
    date_range: Optional[DateRange] = None

    @field_validator("question")
    @classmethod
    def _validate_question(cls, value: str) -> str:
        if not re.search(r"[А-Яа-я]", value):
            raise ValueError("Вопрос должен быть на русском языке.")
        return value

    @model_validator(mode="after")
    def _normalize(self) -> "DBQuestion":
        self.normalized_question = " ".join(self.question.strip().split())
        self.date_range = parse_date_range(self.normalized_question)
        return self


def parse_date_range(question: str) -> Optional[DateRange]:
    range_match = _RANGE_DATE_PATTERN.search(question)
    if range_match:
        month = _MONTHS[range_match.group("month").lower()]
        year = int(range_match.group("year"))
        start_day = int(range_match.group("start_day"))
        end_day = int(range_match.group("end_day"))
        return DateRange(
            start_date=date(year, month, start_day),
            end_date=date(year, month, end_day),
        )

    single_match = _SINGLE_DATE_PATTERN.search(question)
    if single_match:
        month = _MONTHS[single_match.group("month").lower()]
        year = int(single_match.group("year"))
        day = int(single_match.group("day"))
        single_date = date(year, month, day)
        return DateRange(start_date=single_date, end_date=single_date)

    return None