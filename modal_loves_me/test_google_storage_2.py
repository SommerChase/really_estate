from google.cloud import storage
from google.oauth2 import service_account
import modal


# Modal is dope
stub = modal.Stub(name="google-test",
                  image=modal.Image.debian_slim().pip_install(""))


path_to_private_key = ''
client = storage.Client.from_service_account_json(json_credentials_path=path_to_private_key)

# The bucket on GCS in which to write the CSV file
bucket = client.bucket('test-bucket-skytowner')
# The name assigned to the CSV file on GCS
blob = bucket.blob('my_data.csv')
blob.upload_from_string(df.to_csv(), 'text/csv')