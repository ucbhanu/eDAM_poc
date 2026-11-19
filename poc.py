"""POC: authenticate, list a few DAM records, and read one record's metadata."""
from api_client import AprimoClient
from records import field_values, get_record, list_records


def main():
    client = AprimoClient()

    print("Step 1: token")
    client.tokens.get_token()
    print("  OK (client_credentials)")

    print("Step 2: list records")
    page = list_records(client, page_size=5)
    print(f"  totalCount={page.get('totalCount')}")
    for item in page.get("items", []):
        print(f"  - {item.get('id')}  status={item.get('status')}  title={item.get('title')}")

    first_id = page["items"][0]["id"]
    print(f"Step 3: record {first_id} with fields")
    record = get_record(client, first_id)
    fields = {k: v for k, v in field_values(record).items() if v not in (None, "", [])}
    print(f"  {len(fields)} populated fields")
    for name, value in list(fields.items())[:10]:
        print(f"  {name}: {str(value)[:80]}")


if __name__ == "__main__":
    main()
