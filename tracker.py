# Databricks notebook source
import csv
import os

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

TRACKER_COLUMNS = [
    "Approval ID",
    "Title",
    "Asset ID",
    "Record ID",
    "Match Status",
    "Asset URL",
    "Annotation Viewer URL",
    "Downloaded File",
    "Local Folder",
    "Folder Path",
    "Manual Steps Pending",
    "Notes",
]


def _norm(name):
    return "".join(ch for ch in str(name or "").lower() if ch.isalnum())


def read_input(path):
    """Read the asset export list (.xlsx or .csv). Returns list of dicts keyed by tracker column names."""
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8-sig") as f:
            raw = list(csv.DictReader(f))
    else:
        ws = load_workbook(path, read_only=True, data_only=True).active
        rows = list(ws.iter_rows(values_only=True))
        header = rows[0] if rows else []
        raw = [dict(zip(header, r)) for r in rows[1:] if any(c not in (None, "") for c in r)]

    lookup = {_norm(c): c for c in TRACKER_COLUMNS}
    lookup["id"] = "Asset ID"
    result = []
    for row in raw:
        mapped = {}
        for key, value in row.items():
            column = lookup.get(_norm(key))
            if column and value not in (None, ""):
                mapped[column] = str(value).strip()
        result.append(mapped)
    return result


def write_tracker(rows, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Litigation Export"
    ws.append(TRACKER_COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="10384F")
    for row in rows:
        ws.append([row.get(c, "") for c in TRACKER_COLUMNS])
    url_col = TRACKER_COLUMNS.index("Asset URL") + 1
    for r in range(2, ws.max_row + 1):
        cell = ws.cell(row=r, column=url_col)
        if cell.value:
            cell.hyperlink = cell.value
            cell.style = "Hyperlink"
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = min(60, max(12, *(len(str(c.value or "")) for c in col)))
    ws.freeze_panes = "A2"
    wb.save(path)
    return path
