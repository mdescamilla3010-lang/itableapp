"""Parses CSV/Excel files uploaded by a tenant into the same Parrot-shaped
payloads the /sync endpoints already accept, so any POS that can export a
spreadsheet can feed the itable ingestion pipeline without a custom adapter.
"""

import io
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import pandas as pd

from app.schemas.cash_shift import ParrotCashShiftPayload, ParrotCashShiftSyncPayload
from app.schemas.order import ParrotOrderItemPayload, ParrotOrderPayload, ParrotSyncPayload

ORDER_REQUIRED_COLUMNS = ["external_order_id", "external_product_id", "product_name", "order_date"]
CASH_SHIFT_REQUIRED_COLUMNS = ["external_shift_id", "expected_cash", "actual_cash", "shift_start"]


class FileImportError(ValueError):
    """Raised when the uploaded file can't be read at all (bad format, missing columns)."""


def _read_table(file_bytes: bytes, filename: str) -> pd.DataFrame:
    buffer = io.BytesIO(file_bytes)
    lower_name = filename.lower()
    try:
        if lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
            df = pd.read_excel(buffer)
        else:
            df = pd.read_csv(buffer)
    except Exception as exc:  # noqa: BLE001 - surfaced to the user as a 400
        raise FileImportError(f"No se pudo leer el archivo: {exc}") from exc

    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def _require_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise FileImportError(f"Faltan columnas requeridas: {', '.join(missing)}")


def _clean_str(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _to_decimal(value: object, default: Decimal) -> Decimal:
    decimal_value = _to_decimal_or_none(value)
    return default if decimal_value is None else decimal_value


def _to_decimal_or_none(value: object) -> Decimal | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _to_utc_datetime(value: object) -> datetime | None:
    ts = pd.to_datetime(value, errors="coerce")
    if ts is None or pd.isna(ts):
        return None
    py_dt = ts.to_pydatetime()
    if py_dt.tzinfo is None:
        return py_dt.replace(tzinfo=timezone.utc)
    return py_dt.astimezone(timezone.utc)


def parse_orders_file(file_bytes: bytes, filename: str) -> tuple[ParrotSyncPayload, int]:
    """Returns the parsed payload and the count of rows skipped for missing/invalid data."""
    df = _read_table(file_bytes, filename)
    _require_columns(df, ORDER_REQUIRED_COLUMNS)

    groups: dict[str, dict] = {}
    rows_skipped = 0

    for _, row in df.iterrows():
        external_order_id = _clean_str(row.get("external_order_id"))
        external_product_id = _clean_str(row.get("external_product_id"))
        product_name = _clean_str(row.get("product_name"))
        order_date = _to_utc_datetime(row.get("order_date"))

        if not external_order_id or not external_product_id or not product_name or order_date is None:
            rows_skipped += 1
            continue

        item = ParrotOrderItemPayload(
            external_product_id=external_product_id,
            product_name=product_name,
            category_name=_clean_str(row.get("category_name")),
            quantity=int(_to_decimal(row.get("quantity"), Decimal("1"))),
            unit_price=_to_decimal(row.get("unit_price"), Decimal("0")),
            unit_cost=_to_decimal(row.get("unit_cost"), Decimal("0")),
        )

        group = groups.setdefault(
            external_order_id,
            {
                "branch_external_id": _clean_str(row.get("branch_external_id")),
                "branch_name": _clean_str(row.get("branch_name")),
                "staff_external_id": _clean_str(row.get("staff_external_id")),
                "staff_name": _clean_str(row.get("staff_name")),
                "table_name": _clean_str(row.get("table_name")),
                "discount_amount": _to_decimal(row.get("discount_amount"), Decimal("0")),
                "discount_reason": _clean_str(row.get("discount_reason")),
                "payment_method": _clean_str(row.get("payment_method")),
                "status": (_clean_str(row.get("status")) or "COMPLETED").upper(),
                "order_date": order_date,
                "explicit_total": _to_decimal_or_none(row.get("total_amount")),
                "items": [],
            },
        )
        group["items"].append(item)

    orders: list[ParrotOrderPayload] = []
    for external_order_id, group in groups.items():
        subtotal = sum((i.unit_price * i.quantity for i in group["items"]), Decimal("0"))
        total_amount = group["explicit_total"]
        if total_amount is None:
            total_amount = max(subtotal - group["discount_amount"], Decimal("0"))

        orders.append(
            ParrotOrderPayload(
                external_order_id=external_order_id,
                branch_external_id=group["branch_external_id"],
                branch_name=group["branch_name"],
                staff_external_id=group["staff_external_id"],
                staff_name=group["staff_name"],
                table_name=group["table_name"],
                total_amount=total_amount,
                discount_amount=group["discount_amount"],
                discount_reason=group["discount_reason"],
                payment_method=group["payment_method"],
                status=group["status"],
                order_date=group["order_date"],
                items=group["items"],
            )
        )

    return ParrotSyncPayload(orders=orders), rows_skipped


def parse_cash_shifts_file(file_bytes: bytes, filename: str) -> tuple[ParrotCashShiftSyncPayload, int]:
    df = _read_table(file_bytes, filename)
    _require_columns(df, CASH_SHIFT_REQUIRED_COLUMNS)

    shifts: list[ParrotCashShiftPayload] = []
    rows_skipped = 0

    for _, row in df.iterrows():
        external_shift_id = _clean_str(row.get("external_shift_id"))
        expected_cash = _to_decimal_or_none(row.get("expected_cash"))
        actual_cash = _to_decimal_or_none(row.get("actual_cash"))
        shift_start = _to_utc_datetime(row.get("shift_start"))

        if not external_shift_id or expected_cash is None or actual_cash is None or shift_start is None:
            rows_skipped += 1
            continue

        shifts.append(
            ParrotCashShiftPayload(
                external_shift_id=external_shift_id,
                staff_external_id=_clean_str(row.get("staff_external_id")),
                staff_name=_clean_str(row.get("staff_name")),
                expected_cash=expected_cash,
                actual_cash=actual_cash,
                shift_start=shift_start,
                shift_end=_to_utc_datetime(row.get("shift_end")),
            )
        )

    return ParrotCashShiftSyncPayload(shifts=shifts), rows_skipped
