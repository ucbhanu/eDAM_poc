import os
import re
import time

TERMINAL_STATES = ("Success", "Failed", "Cancelled")


def latest_master_file(client, record_id):
    record = client.get(f"record/{record_id}", headers={"select-record": "masterfilelatestversion"})
    return record.get("masterFileLatestVersion") or {}


def file_versions(client, record_id):
    files = client.get(f"record/{record_id}/files").get("items", [])
    versions = []
    for f in files:
        versions.extend(client.get(f"file/{f['id']}/fileversions").get("items", []))
    return sorted(versions, key=lambda v: v.get("versionNumber") or 0)


def create_download_order(client, record_id, timeout=120, poll=3):
    order = client.post(
        "orders",
        json={
            "type": "download",
            "targets": [{"recordId": record_id, "targetTypes": ["Document"], "assetType": "LatestVersionOfMasterFile"}],
        },
    )
    deadline = time.time() + timeout
    while order.get("status") not in TERMINAL_STATES:
        if time.time() > deadline:
            raise TimeoutError(f"Download order {order.get('id')} not ready after {timeout}s")
        time.sleep(poll)
        order = client.get(f"order/{order['id']}")
    if order["status"] != "Success":
        raise RuntimeError(f"Download order {order['id']} {order['status']}: {order.get('message')}")
    return order["deliveredFiles"]


def _safe_name(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip() or "download"


def download_latest(client, record_id, dest_dir, file_name=None):
    """Download the latest master file of a record into dest_dir. Returns the saved path."""
    master = latest_master_file(client, record_id)
    file_name = _safe_name(file_name or master.get("fileName") or record_id)
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, file_name)

    for url in create_download_order(client, record_id):
        # Delivered URLs carry their own download token; no bearer header needed.
        with client.session.get(url, stream=True, timeout=300) as resp:
            resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
    return path
