from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedMeasurement:
    field: str
    normalized_value: float
    normalized_unit: str
    original_value: str
    original_unit: str


def _parse_decimal(raw: str) -> float:
    return float(raw.replace(",", ".").strip())


def parse_weight(text: str) -> Optional[ParsedMeasurement]:
    t = text.lower()
    patterns = [
        (r"(\d+(?:[.,]\d+)?)\s*(kg|kgs|kilo|kilos|kilogramo|kilogramos)\b", "kg"),
        (r"(\d+(?:[.,]\d+)?)\s*(lb|lbs|libra|libras|pound|pounds)\b", "lb"),
    ]
    for pattern, detected_unit in patterns:
        match = re.search(pattern, t, re.I)
        if not match:
            continue
        raw_value = match.group(1)
        value = _parse_decimal(raw_value)
        value_kg = value if detected_unit == "kg" else value * 0.45359237
        return ParsedMeasurement(
            field="weight_kg",
            normalized_value=round(value_kg, 2),
            normalized_unit="kg",
            original_value=raw_value,
            original_unit=match.group(2),
        )
    if not re.search(r"\b(peso|pesar|pesa)\b", t) and not re.search(
        r"\b(kg|kilo|kilos|lb|lbs|libras)\b", t
    ):
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)\b", t)
    if not match:
        return None
    value = _parse_decimal(match.group(1))
    return ParsedMeasurement(
        field="weight_kg",
        normalized_value=round(value, 2),
        normalized_unit="kg",
        original_value=match.group(1),
        original_unit="kg",
    )


def parse_height(text: str) -> Optional[ParsedMeasurement]:
    t = text.lower().strip()

    feet_inches = re.search(
        r"(\d+)\s*(?:ft|feet|pie|pies|')\s*(\d+(?:[.,]\d+)?)?\s*(?:in|inch|inches|pulgada|pulgadas|\")?",
        t,
        re.I,
    )
    if feet_inches:
        feet = int(feet_inches.group(1))
        inch_raw = feet_inches.group(2)
        inches = _parse_decimal(inch_raw) if inch_raw else 0.0
        total_cm = feet * 30.48 + inches * 2.54
        if inch_raw:
            orig = f"{feet}'{inch_raw}"
        else:
            orig = f"{feet}'"
        return ParsedMeasurement(
            field="height_cm",
            normalized_value=round(total_cm, 2),
            normalized_unit="cm",
            original_value=orig,
            original_unit="ft/in",
        )

    patterns = [
        (
            r"(\d+(?:[.,]\d+)?)\s*(cm|cms|centimetro|centimetros|centímetro|centímetros)\b",
            "cm",
        ),
        (r"(\d+(?:[.,]\d+)?)\s*(m|mt|mts|metro|metros)\b", "m"),
    ]
    for pattern, detected_unit in patterns:
        match = re.search(pattern, t, re.I)
        if not match:
            continue
        raw_value = match.group(1)
        value = _parse_decimal(raw_value)
        value_cm = value if detected_unit == "cm" else value * 100
        return ParsedMeasurement(
            field="height_cm",
            normalized_value=round(value_cm, 2),
            normalized_unit="cm",
            original_value=raw_value,
            original_unit=match.group(2),
        )

    if not re.search(
        r"\b(estatura|altura|talla|stature|height)\b", t
    ) and not re.search(r"\b(cm|metro|metros|pies|ft|pulg)\b", t):
        return None

    match = re.search(r"(\d+(?:[.,]\d+)?)\b", t)
    if not match:
        return None
    value = _parse_decimal(match.group(1))
    value_cm = value if value >= 3 else value * 100
    original_unit = "cm" if value >= 3 else "m"
    return ParsedMeasurement(
        field="height_cm",
        normalized_value=round(value_cm, 2),
        normalized_unit="cm",
        original_value=match.group(1),
        original_unit=original_unit,
    )


def measurement_in_reasonable_range(parsed: ParsedMeasurement) -> bool:
    if parsed.field == "weight_kg":
        return 20 <= parsed.normalized_value <= 400
    if parsed.field == "height_cm":
        return 80 <= parsed.normalized_value <= 250
    return False
