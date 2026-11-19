# Databricks notebook source
"""US Litigation Activity export workflow.

Automates the API-capable parts of the "US Litigation Activity Process":
  Step 1  Find each asset by Approval ID (fallback: Title, validated by Asset ID) and fill Asset URL
  Step 2  Create the local export folder per asset and download the latest master file
  Step 3  Write the tracker Excel (Asset URL, local folder, pending manual steps)

Manual steps (no public API): annotated version export from the Annotation Viewer,
Audit Report (Reports -> Task Report LMR CH), SharePoint upload and Folder Path link.
"""
import argparse
import logging
import os
from datetime import datetime

from api_client import AprimoClient
from asset_download import download_latest
from asset_search import APPROVAL_ID_FIELD, TITLE_FIELD, asset_url, find_by_approval_id, find_by_title
from records import field_values
from tracker import read_input, write_tracker

log = logging.getLogger("litigation")

MANUAL_STEPS = (
    "Annotation Viewer URL; export annotated versions as Version_1..n; "
    "Audit Report <Approval ID>_Audit_Report (Excel+PDF); SharePoint upload; Folder Path link"
)


def resolve_asset(client, row):
    """Return (record, status). Approval ID first, then Title; Asset ID disambiguates."""
    approval_id, title, asset_id = row.get("Approval ID"), row.get("Title"), row.get("Asset ID")
    matches, source = [], None
    if approval_id:
        matches, source = find_by_approval_id(client, approval_id), "Approval ID"
    if not matches and title:
        matches, source = find_by_title(client, title), "Title"
    if asset_id:
        matches = [m for m in matches if m["id"].lower() == asset_id.lower()] or matches
    if not matches:
        return None, "Not found"
    if len(matches) > 1:
        return None, f"Multiple matches by {source} ({len(matches)}) - add Asset ID"
    return matches[0], f"Matched by {source}"


def process_row(client, row, out_dir, download):
    result = dict(row)
    record, status = resolve_asset(client, row)
    result["Match Status"] = status
    result["Manual Steps Pending"] = MANUAL_STEPS
    if not record:
        log.warning("  %s: %s", row.get("Approval ID") or row.get("Title"), status)
        return result

    fields = field_values(record)
    approval_id = row.get("Approval ID") or fields.get(APPROVAL_ID_FIELD) or record["id"]
    result.update({
        "Approval ID": approval_id,
        "Title": row.get("Title") or fields.get(TITLE_FIELD) or "",
        "Record ID": record["id"],
        "Asset URL": asset_url(record["id"]),
    })
    folder = os.path.join(out_dir, approval_id)
    os.makedirs(folder, exist_ok=True)
    result["Local Folder"] = os.path.abspath(folder)

    if download:
        try:
            path = download_latest(client, record["id"], folder)
            result["Downloaded File"] = os.path.basename(path)
            log.info("  %s: downloaded %s (%s bytes)", approval_id, result["Downloaded File"], os.path.getsize(path))
        except Exception as exc:
            result["Notes"] = f"Download failed: {exc}"
            log.warning("  %s: download failed: %s", approval_id, exc)
    log.info("  %s: %s -> %s", approval_id, status, result["Asset URL"])
    return result


def main():
    parser = argparse.ArgumentParser(description="US Litigation Activity export")
    parser.add_argument("input", nargs="?", default=os.getenv("INPUT_FILE"),
                        help="asset export list (.xlsx or .csv) with Approval ID / Title / Asset ID columns (default: INPUT_FILE in .env)")
    parser.add_argument("--out", default=os.path.join("output", "litigation"))
    parser.add_argument("--no-download", action="store_true", help="only resolve assets and URLs")
    args = parser.parse_args()
    if not args.input:
        parser.error("input file required (argument or INPUT_FILE in .env)")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_dir = os.path.join(args.out, datetime.now().strftime("%Y%m%d_%H%M%S"))

    log.info("Step 1/3: read input %s", args.input)
    rows = read_input(args.input)
    log.info("  %s rows", len(rows))

    log.info("Step 2/3: resolve assets%s", "" if args.no_download else " and download latest master files")
    client = AprimoClient()
    results = [process_row(client, row, run_dir, not args.no_download) for row in rows]

    log.info("Step 3/3: write tracker")
    tracker = write_tracker(results, os.path.join(run_dir, "Litigation_Export_Tracker.xlsx"))
    found = sum(1 for r in results if r.get("Record ID"))
    downloaded = sum(1 for r in results if r.get("Downloaded File"))
    log.info("  %s", os.path.abspath(tracker))
    log.info("Done: %s rows, %s matched, %s downloaded", len(results), found, downloaded)


if __name__ == "__main__":

    main()
