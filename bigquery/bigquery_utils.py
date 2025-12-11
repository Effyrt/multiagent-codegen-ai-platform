from google.cloud import bigquery

client = bigquery.Client()

def insert_rows(table_id, rows):
    """
    table_id: 'project.dataset.table'
    rows: list of dict
    """
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        print("Insert errors:", errors)
    else:
        print("Inserted into BigQuery:", table_id)
