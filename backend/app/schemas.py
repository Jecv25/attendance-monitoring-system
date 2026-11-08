from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Role = Literal['admin', 'teacher', 'supervisor']
Status = Literal['present', 'late', 'absent', 'excused']
Password = Annotated[str, StringConstraints(strip_whitespace=False, min_length=12, max_length=128)]


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Login(Strict):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=1, max_length=128)
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=False)


class UserCreate(Strict):
    username: str = Field(pattern=r'^[a-z][a-z0-9_.-]{2,39}$')
    display_name: str = Field(min_length=2, max_length=80)
    password: Password
    role: Role


class UserUpdate(Strict):
    display_name: str = Field(min_length=2, max_length=80)
    role: Role
    active: bool


class PasswordReset(Strict):
    password: Password


class StudentInput(Strict):
    student_code: str = Field(pattern=r'^[A-Za-z0-9-]{2,30}$')
    display_name: str = Field(min_length=2, max_length=80)
    active: bool = True


class ClassInput(Strict):
    code: str = Field(pattern=r'^[A-Za-z0-9-]{2,30}$')
    title: str = Field(min_length=2, max_length=100)
    teacher_id: int = Field(gt=0)


class RosterInput(Strict):
    student_ids: list[int] = Field(max_length=100)

    @model_validator(mode='after')
    def unique(self):
        if any(x <= 0 for x in self.student_ids) or len(set(self.student_ids)) != len(self.student_ids):
            raise ValueError('Roster identifiers must be positive and unique')
        return self


class SessionInput(Strict):
    class_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=100)
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode='after')
    def times(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError('An explicit timezone is required')
        duration = (self.ends_at - self.starts_at).total_seconds()
        if duration <= 0 or duration > 86400:
            raise ValueError('Session duration must be greater than zero and at most 24 hours')
        return self


class Entry(Strict):
    student_id: int = Field(gt=0)
    status: Status


class AttendanceInput(Strict):
    version: int = Field(ge=0)
    items: list[Entry] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def unique(self):
        if len({x.student_id for x in self.items}) != len(self.items):
            raise ValueError('Duplicate students in attendance submission')
        return self


class VersionInput(Strict):
    version: int = Field(ge=0)


class CorrectionInput(Entry):
    version: int = Field(ge=0)
    reason: str = Field(min_length=8, max_length=240)


class Envelope(Strict):
    message_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    issued_at: int
    expires_at: int
    key_version: str = Field(min_length=1, max_length=20)
    nonce: str = Field(min_length=16, max_length=24)
    ciphertext: str = Field(min_length=24, max_length=200000)
