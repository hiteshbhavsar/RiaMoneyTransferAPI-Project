#!/usr/bin/env python3
"""تحليل اتجاهات حوالات RIA من CSV مع دعم الأسهم والترميزات المختلفة."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable

DEFAULT_INPUT = Path("/home/ubuntu/upload/ria_full_report_2026-09-01(8).csv")

# ترميزات تُجرَّب بالترتيب: UTF-8 (مع/بدون BOM)، UTF-16 من Excel، ثم Windows-1256 العربي.
CANDIDATE_ENCODINGS = ("utf-8-sig", "utf-16", "cp1256")

# أكواد RIA قد تكون رقمية فقط أو تبدأ برمز دولة/منطقة، مثل IT9314773257.
TRANSFER_CODE_RE = re.compile(r"^[A-Z]{2}\d{8,14}$")
NUMERIC_PIN_RE = re.compile(r"^\d{8,14}$")
EMBEDDED_CODE_RE = re.compile(r"(?<![A-Z0-9])([A-Z]{2}\s*-?\s*\d{8,14}|\d{8,14})(?![A-Z0-9])")

# الأسهم الشائعة في ملفات CSV، بما فيها أسهم Unicode. الأطول أولًا حتى لا يبتلع ">" جزءًا من "-->".
ARROW_RE = re.compile(
    r"(?:-->|—>|–>|->|=>|→|➜|➔|➡|⟶|⟹|⇒|⟾|➞|➝|➙|➛|➢|➣|↦|⇢|﹥|＞|>)"
)

# فاصل بديل يظهر أحيانًا بعد إزالة السهم من نص CSV.
SEPARATOR_RE = re.compile(r"\s*(?:/|\\|\||;|::|\s+-\s+)\s*")

COUNTRY_ALIASES = {
    "TR": "TR", "TUR": "TR", "TURKEY": "TR", "TURKIYE": "TR", "TURQUIE": "TR",
    "تركيا": "TR", "تركيه": "TR",
    "EG": "EG", "EGY": "EG", "EGYPT": "EG", "مصر": "EG",
    "MA": "MA", "MAR": "MA", "MOROCCO": "MA", "المغرب": "MA",
    "DZ": "DZ", "DZA": "DZ", "ALGERIA": "DZ", "الجزائر": "DZ",
    "TN": "TN", "TUN": "TN", "TUNISIA": "TN", "تونس": "TN",
    "LB": "LB", "LBN": "LB", "LEBANON": "LB", "لبنان": "LB",
    "IQ": "IQ", "IRQ": "IQ", "IRAQ": "IQ", "العراق": "IQ",
    "SY": "SY", "SYR": "SY", "SYRIA": "SY", "سوريا": "SY", "سورية": "SY",
    "JO": "JO", "JOR": "JO", "JORDAN": "JO", "الاردن": "JO",
}

TURKEY_CODES = {"TR"}

CODE_COLUMNS = (
    "pin", "order number", "order no", "ordernumber", "reference",
    "reference number", "code", "transfer code", "رقم الحوالة", "رقم الطلب",
    "الكود", "المرجع",
)
STATUS_COLUMNS = ("الحالة", "status", "transfer status", "حالة الحوالة")


def clean_text(value: object) -> str:
    """إزالة BOM ومحارف الاتجاه والمسافات غير الطبيعية من قيمة CSV."""
    text = "" if value is None else str(value)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")  # يشمل BOM و RLM/LRM
    text = text.replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def _fold(text: str) -> str:
    """إزالة علامات التشكيل اللاتينية والعربية وتوحيد الألف، للمطابقة فقط."""
    # İ تتحول إلى I + نقطة مركّبة، فتُزال النقطة مع بقية العلامات.
    decomposed = unicodedata.normalize("NFKD", text.upper())
    folded = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub("[أإآ]", "ا", folded)


def normalize_country(value: object) -> str:
    text = clean_text(value).strip(" .,:;()[]{}")
    if not text:
        return ""
    return COUNTRY_ALIASES.get(_fold(text), text.upper())


def normalize_transfer_code(value: object) -> str:
    """توحيد كود التحويل مع الإبقاء على بادئة الأحرف مثل IT."""
    text = clean_text(value).upper()
    # تسمح بعض التقارير بمسافة أو شرطة بين البادئة والأرقام.
    return re.sub(r"[\s-]+", "", text)


def is_transfer_code(value: object) -> bool:
    code = normalize_transfer_code(value)
    return bool(NUMERIC_PIN_RE.fullmatch(code) or TRANSFER_CODE_RE.fullmatch(code))


def _normalized_keys(row: dict[str, str]) -> dict[str, str]:
    return {clean_text(k).lower(): k for k in row if k is not None}


def code_from_row(row: dict[str, str]) -> str:
    """العثور على PIN/Order Number/Code حتى لو كان الكود أبجديًا رقميًا.

    إن وُجد عمود كود معروف نبحث فيه فقط؛ وإلا نمسح كل الأعمدة كحل أخير
    (قد يلتقط ذلك أرقامًا أخرى كالهواتف، لذلك لا يُستخدم إلا عند غياب عمود الكود).
    """
    keys = _normalized_keys(row)
    candidates = [row.get(keys[name]) for name in CODE_COLUMNS if name in keys]
    if not candidates:
        candidates = list(row.values())
    for candidate in candidates:
        if isinstance(candidate, list):  # أعمدة زائدة بلا ترويسة في DictReader
            candidate = " ".join(candidate)
        if is_transfer_code(candidate):
            return normalize_transfer_code(candidate)
        # استخراج كود مضمّن داخل نص مثل "Order: IT9314773257".
        match = EMBEDDED_CODE_RE.search(clean_text(candidate).upper())
        if match and is_transfer_code(match.group(1)):
            return normalize_transfer_code(match.group(1))
    return ""


def split_route(value: object) -> list[str]:
    """تحويل تمثيلات المسار المختلفة إلى قائمة [بلد المصدر، بلد الوجهة]."""
    route = clean_text(value)
    if not route:
        return []
    parts = [p for p in ARROW_RE.split(route) if clean_text(p)]
    if len(parts) < 2:
        parts = [p for p in SEPARATOR_RE.split(route) if clean_text(p)]
    return [normalize_country(part) for part in parts[:2]]


def route_from_row(row: dict[str, str]) -> tuple[str, str, list[str]]:
    """استخراج المصدر والوجهة من أعمدة صريحة أو من عمود المسار."""
    keys = _normalized_keys(row)

    def column(*names: str) -> str:
        for name in names:
            key = keys.get(name.lower())
            if key is not None and clean_text(row.get(key)):
                return clean_text(row[key])
        return ""

    source = column("from", "source", "countryfrom", "country from", "بلد المصدر", "بلد الإرسال", "من")
    destination = column("to", "destination", "countryto", "country to", "بلد الوجهة", "بلد الاستلام", "إلى")
    if source or destination:
        parts = [normalize_country(source), normalize_country(destination)]
    else:
        parts = split_route(column("المسار", "route", "transfer route", "الاتجاه", "direction"))

    source = parts[0] if parts else ""
    destination = parts[1] if len(parts) > 1 else ""
    return source, destination, parts


def enrich(row: dict[str, str]) -> dict:
    """نسخة من الصف مع حقول مطبّعة للتحليل، دون تعديل الصف الأصلي."""
    source, destination, parts = route_from_row(row)
    enriched = dict(row)
    enriched.pop(None, None)  # خلايا زائدة بلا ترويسة لا تُسلسل في JSON بمفتاح None
    enriched["_normalized_from"] = source
    enriched["_normalized_to"] = destination
    enriched["_normalized_route"] = " → ".join(p or "?" for p in parts) if any(parts) else "-"
    enriched["_normalized_code"] = code_from_row(row)
    enriched["_code_valid"] = bool(enriched["_normalized_code"])
    return enriched


def rows_for_direction(rows: Iterable[dict]) -> tuple[list[dict], list[dict]]:
    """فصل الصفوف المطبّعة إلى (من تركيا، إلى تركيا)."""
    from_turkey, to_turkey = [], []
    for row in rows:
        if row["_normalized_from"] in TURKEY_CODES:
            from_turkey.append(row)
        if row["_normalized_to"] in TURKEY_CODES:
            to_turkey.append(row)
    return from_turkey, to_turkey


def status_of(row: dict) -> str:
    keys = _normalized_keys(row)
    for name in STATUS_COLUMNS:
        key = keys.get(name)
        if key is not None and clean_text(row[key]):
            return clean_text(row[key])
    return "-"


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], str]:
    """قراءة CSV بأول ترميز ينجح، مع اكتشاف الفاصل (, ; tab |)."""
    raw = path.read_bytes()
    for encoding in CANDIDATE_ENCODINGS:
        # بدون BOM قد يفك utf-16 أي بايتات زوجية الطول إلى نص عشوائي، لذا نشترط وجوده.
        if encoding == "utf-16" and not raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            continue
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        break
    else:
        raise ValueError(f"تعذّر فك ترميز الملف بأي من: {', '.join(CANDIDATE_ENCODINGS)}")

    text = text.lstrip("﻿")
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(io.StringIO(text, newline=""), dialect=dialect)), encoding


def analyze(path: Path) -> dict:
    rows, encoding = read_csv_rows(path)
    enriched_rows = [enrich(row) for row in rows]
    from_turkey, to_turkey = rows_for_direction(enriched_rows)
    all_codes = [row["_normalized_code"] for row in enriched_rows if row["_code_valid"]]
    code_counts = Counter(all_codes)

    return {
        "input_file": str(path),
        "encoding": encoding,
        "total_rows": len(rows),
        "valid_code_count": len(all_codes),
        "invalid_or_missing_code_count": len(rows) - len(all_codes),
        "code_counts": dict(code_counts),
        "duplicate_codes": {code: n for code, n in code_counts.items() if n > 1},
        "from_turkey_count": len(from_turkey),
        "to_country_counts": dict(Counter(row["_normalized_to"] or "-" for row in from_turkey)),
        "status_counts": dict(Counter(status_of(row) for row in from_turkey)),
        "rows": from_turkey,
        "to_turkey_count": len(to_turkey),
        "from_country_counts_to_turkey": dict(Counter(row["_normalized_from"] or "-" for row in to_turkey)),
        "to_turkey_status_counts": dict(Counter(status_of(row) for row in to_turkey)),
        "to_turkey_rows": to_turkey,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="تحليل اتجاهات حوالات RIA من ملف CSV")
    parser.add_argument("csv_file", nargs="?", type=Path, default=DEFAULT_INPUT, help="مسار ملف CSV")
    parser.add_argument("--output", type=Path, help="حفظ JSON بدل طباعته فقط")
    args = parser.parse_args()

    if not args.csv_file.is_file():
        parser.error(f"ملف CSV غير موجود: {args.csv_file}")

    try:
        report = analyze(args.csv_file)
    except ValueError as exc:
        parser.error(str(exc))

    result = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(result + "\n", encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()
