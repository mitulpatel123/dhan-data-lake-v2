"""Domain models and validation rules for raw market bars."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


class ValidationError(ValueError):
    """Raised when a source record violates the raw market-bar contract."""


def _required_text(record: Mapping[str, Any], field: str) -> str:
    value = str(record.get(field, "")).strip()
    if not value:
        raise ValidationError(f"{field} is required")
    return value


def _decimal(record: Mapping[str, Any], field: str) -> Decimal:
    try:
        return Decimal(str(record.get(field, "")).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field} must be a decimal") from exc


@dataclass(frozen=True, slots=True)
class MarketBar:
    security_id: str
    symbol: str
    exchange_segment: str
    interval: str
    event_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    source: str = "sample"

    @classmethod
    def from_mapping(cls, record: Mapping[str, Any]) -> "MarketBar":
        timestamp = _required_text(record, "event_time")
        try:
            event_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError("event_time must be ISO-8601") from exc
        if event_time.tzinfo is None:
            raise ValidationError("event_time must include a timezone")

        try:
            volume = int(str(record.get("volume", "")).strip())
        except ValueError as exc:
            raise ValidationError("volume must be an integer") from exc

        bar = cls(
            security_id=_required_text(record, "security_id"),
            symbol=_required_text(record, "symbol").upper(),
            exchange_segment=_required_text(record, "exchange_segment").upper(),
            interval=_required_text(record, "interval").lower(),
            event_time=event_time,
            open=_decimal(record, "open"),
            high=_decimal(record, "high"),
            low=_decimal(record, "low"),
            close=_decimal(record, "close"),
            volume=volume,
            source=str(record.get("source", "sample")).strip() or "sample",
        )
        bar.validate()
        return bar

    def validate(self) -> None:
        prices = (self.open, self.high, self.low, self.close)
        if any(value < 0 for value in prices):
            raise ValidationError("prices cannot be negative")
        if self.high < max(self.open, self.close, self.low):
            raise ValidationError("high must be greater than or equal to OHLC values")
        if self.low > min(self.open, self.close, self.high):
            raise ValidationError("low must be less than or equal to OHLC values")
        if self.volume < 0:
            raise ValidationError("volume cannot be negative")

    @property
    def natural_key(self) -> tuple[str, str, datetime]:
        return self.security_id, self.interval, self.event_time

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["event_time"] = self.event_time.isoformat()
        for field in ("open", "high", "low", "close"):
            result[field] = str(result[field])
        return result
