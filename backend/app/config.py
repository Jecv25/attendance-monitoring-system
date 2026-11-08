"""Environment-owned configuration. No confidential defaults."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    database: str = str(ROOT / '.local' / 'attendance.db')
    secure_cookies: bool = False
    environment: str = 'development'
    origins: tuple[str, ...] = ('http://127.0.0.1:7357', 'http://127.0.0.1:8000', 'https://localhost:8443')
    session_seconds: int = 3600
    report_key: str = ''
    key_version: str = 'v1'
    login_limit: int = 8
    login_window: int = 900
    reminder_seconds: int = 900
    overdue_seconds: int = 600
    escalation_seconds: int = 1800
    worker_stale_seconds: int = 45
    notification_timeout: float = 2.0
    retention_days: int = 90

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / '.env', override=False)
        settings = cls(
            database=os.getenv('ATTENDANCE_DATABASE', cls.database),
            secure_cookies=os.getenv('ATTENDANCE_SECURE_COOKIES', 'false').lower() == 'true',
            environment=os.getenv('ATTENDANCE_ENVIRONMENT', 'development'),
            origins=tuple(x.strip() for x in os.getenv('ATTENDANCE_ORIGINS', ','.join(cls.origins)).split(',') if x.strip()),
            report_key=os.getenv('ATTENDANCE_REPORT_KEY', ''),
            key_version=os.getenv('ATTENDANCE_KEY_VERSION', 'v1'),
        )
        if settings.environment != 'development' and not settings.secure_cookies:
            raise ValueError('HTTPS secure cookies are required outside development')
        if not settings.origins or '*' in settings.origins:
            raise ValueError('Explicit trusted origins are required')
        return settings
