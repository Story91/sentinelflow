"""Boundary validation for CSV or streaming records."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from sentinelflow.domain.schemas import DomainValidationError, Transaction


@dataclass(slots=True)
class ValidationReport:
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return self.invalid_rows == 0 and self.valid_rows > 0


def validate_records(
    records: Iterable[Mapping[str, object]],
) -> tuple[list[Transaction], ValidationReport]:
    valid: list[Transaction] = []
    report = ValidationReport()
    for row_number, record in enumerate(records, start=2):
        report.total_rows += 1
        try:
            valid.append(Transaction.from_mapping(record))
            report.valid_rows += 1
        except (DomainValidationError, TypeError, ValueError) as exc:
            report.invalid_rows += 1
            if len(report.errors) < 20:
                report.errors.append(f"row {row_number}: {exc}")
    return valid, report


def read_transactions(
    path: Path, *, require_labels: bool = False
) -> tuple[list[Transaction], ValidationReport]:
    with path.open("r", newline="", encoding="utf-8") as stream:
        rows = csv.DictReader(stream)
        transactions, report = validate_records(rows)
    if require_labels:
        unlabeled = sum(event.is_fraud is None for event in transactions)
        if unlabeled:
            report.invalid_rows += unlabeled
            report.valid_rows -= unlabeled
            transactions = [event for event in transactions if event.is_fraud is not None]
            report.errors.append(f"{unlabeled} rows are missing is_fraud")
    return transactions, report
