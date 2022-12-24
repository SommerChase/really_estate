import json
import os
import pandas as pd
import modal

stub = modal.Stub(image=modal.Image.debian_slim().pip_install("google-cloud-storage", "pandas"))
#df = pd.read_csv("../data_flows_output/2022-12-03_zillow_scrape_output.csv")
df = pd.DataFrame(data=[{1,2,3},{4,5,6}],columns=['a','b','c'])

@stub.function(secret=modal.Secret.from_name("my-googlecloud-secret"))
def upload_to_google_cloud_storage(zillow_df):
    # from google.cloud import bigquery
    from google.oauth2 import service_account
    from google.cloud import storage

    service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    client = storage.Client(credentials=credentials)
    bucket = client.get_bucket('really-estate-bucket')
    bucket.blob('upload_test/test.csv').upload_from_string(zillow_df.to_csv(), 'text/csv')

if __name__ == "__main__":
    with stub.run():
        upload_to_google_cloud_storage(df)