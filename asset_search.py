import config

APPROVAL_ID_FIELD = "byr_approvalId"
TITLE_FIELD = "byr_Title"


def _quote(value):
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def search_records(client, expression, page_size=25):
    result = client.post(
        "search/records",
        json={"searchExpression": {"expression": expression}},
        headers={"pageSize": str(page_size), "select-record": "fields"},
    )
    return result.get("items", [])


def find_by_approval_id(client, approval_id):
    return search_records(client, f"FieldName('{APPROVAL_ID_FIELD}') = {_quote(approval_id)}")


def find_by_title(client, title):
    return search_records(client, f"FieldName('{TITLE_FIELD}') = {_quote(title)}")


def asset_url(record_id):
    return f"{config.DAM_UI_URL}contentitems/{record_id}"
