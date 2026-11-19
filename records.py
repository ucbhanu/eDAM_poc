def list_records(client, page=1, page_size=10):
    return client.get("records", headers={"page": str(page), "pageSize": str(page_size)})


def get_record(client, record_id, expand=("fields",)):
    return client.get(f"record/{record_id}", headers={"select-record": ",".join(expand)})


def field_values(record):
    """Flatten the expanded `fields` of a record into {fieldName: first value}."""
    result = {}
    for field in (record.get("fields") or {}).get("items", []):
        values = field.get("localizedValues") or []
        first = values[0] if values else {}
        result[field.get("fieldName")] = first.get("value", first.get("values"))
    return result
