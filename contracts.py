"""Core contracts and shared data models for the DamaDam scraper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Protocol

try:
    from typing import Literal
except ImportError:  # Python <3.8 compatibility fallback
    Literal = str  # type: ignore


SCRAPE_STATUS_SUCCESS = "success"
SCRAPE_STATUS_SKIPPED = "skipped"
SCRAPE_STATUS_ERROR = "error"


@dataclass(frozen=True)
class ScrapeResult:
    """Unified result contract produced by scrapers."""

    status: "Literal['success', 'skipped', 'error']"
    data: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    skip_reason: Optional[str] = None

    def is_success(self) -> bool:
        return self.status == SCRAPE_STATUS_SUCCESS

    def is_skipped(self) -> bool:
        return self.status == SCRAPE_STATUS_SKIPPED

    def is_error(self) -> bool:
        return self.status == SCRAPE_STATUS_ERROR


STATS_KEYS = (
    "new",
    "updated",
    "unchanged",
    "failed",
    "skipped",
    "logged",
    "processed",
    "total_found",
    "success",
)


def create_stats_snapshot() -> Dict[str, int]:
    """Create a stats dictionary pre-populated with required keys."""

    stats = {key: 0 for key in STATS_KEYS}
    # Retain legacy counters for backward compatibility
    stats.update({
        "invalid_nicknames": 0,
        "error": 0,
    })
    return stats


class PersistenceAdapter(Protocol):
    """Persistence layer contract implemented by Sheets / CSV / dry-run adapters."""

    def get_profile(self, nickname: str) -> Optional[Dict[str, str]]:
        ...

    def create_profile(self, profile: Dict[str, str]) -> Dict[str, str]:
        ...

    def update_profile(self, nickname: str, profile: Dict[str, str]) -> Dict[str, str]:
        ...

    def upsert_profile(self, profile: Dict[str, str]) -> Dict[str, str]:
        ...

    def update_dashboard(self, metrics: Dict[str, int]) -> None:
        ...

    def log_online_user(self, nickname: str, timestamp: Optional[str] = None) -> None:
        ...

    def get_pending_targets(self) -> list:
        ...

    def update_target_status(self, row: int, status: str, remarks: str) -> None:
        ...
*** End Patch
