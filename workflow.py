"""Workflow: export DAM record metadata to CSV and JSON (read-only).

Steps:
  1. Authenticate (client_credentials)
  2. Page through records
  3. Fetch each record's fields
  4. Write output/records_<timestamp>.csv and .json
"""
import argparse
import csv
import json
import logging
import os
from datetime import datetime

from api_client import AprimoClient
from records import field_values, get_record, list_records

log = logging.getLogger("workflow")


def step_authenticate(client):
    log.info("Step 1/4: authenticate")
    client.tokens.get_token()
    log.info("  token OK")


def step_collect_ids(client, max_records, page_size):
    log.info("Step 2/4: list records (max=%s)", max_records)
    ids, page = [], 1
    while len(ids) < max_records:
        result = list_records(client, page=page, page_size=page_size)
        items = result.get("items", [])
        if not items:
            break
        ids.extend(item["id"] for item in items)
        log.info("  page %s: %s ids (total available %s)", page, len(items), result.get("totalCount"))
        page += 1
    return ids[:max_records]


def step_fetch_metadata(client, ids):
    log.info("Step 3/4: fetch fields for %s records", len(ids))
    rows = []
    for i, record_id in enumerate(ids, 1):
        try:
            record = get_record(client, record_id)
            rows.append({"id": record_id, "status": record.get("status"), **field_values(record)})
        except Exception as exc:
            log.warning("  %s failed: %s", record_id, exc)
        if i % 10 == 0:
            log.info("  %s/%s", i, len(ids))
    return rows


def step_export(rows, out_dir):
    log.info("Step 4/4: export")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(out_dir, f"records_{stamp}.json")
    csv_path = os.path.join(out_dir, f"records_{stamp}.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    columns = sorted({key for row in rows for key in row}, key=lambda c: (c not in ("id", "status"), c))
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in row.items()})

    log.info("  %s", json_path)
    log.info("  %s", csv_path)


def main():
    parser = argparse.ArgumentParser(description="Export Aprimo DAM record metadata")
    parser.add_argument("--max", type=int, default=20, help="maximum records to export")
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--out", default="output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    client = AprimoClient()
    step_authenticate(client)
    ids = step_collect_ids(client, args.max, min(args.page_size, args.max))
    rows = step_fetch_metadata(client, ids)
    step_export(rows, args.out)
    log.info("Done: %s records exported", len(rows))


if __name__ == "__main__":
    main()
