import json
import os

import modal

stub = modal.Stub(image=modal.Image.debian_slim().pip_install("google-cloud-bigquery"))


@stub.function(secret=modal.Secret.from_name("my-googlecloud-secret"))
def query():
    from google.cloud import bigquery
    from google.oauth2 import service_account

    service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    client = bigquery.Client(credentials=credentials)

    # Run a query against a public dataset with name US first name statistics
    query = """
        SELECT name, SUM(number) as total_people
        FROM `bigquery-public-data.usa_names.usa_1910_2013`
        WHERE state = 'TX'
        GROUP BY name, state
        ORDER BY total_people DESC
        LIMIT 20
    """
    query_job = client.query(query)
    return {row["name"]: row["total_people"] for row in query_job}


if __name__ == "__main__":
    with stub.run():
        print(query.call())
        # This will print {'James': 272793, 'John': 235139, 'Michael': 225320, ...
