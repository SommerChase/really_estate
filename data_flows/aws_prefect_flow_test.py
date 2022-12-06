from prefect import flow
from prefect_aws import AwsCredentials
from prefect_aws.s3 import s3_upload

@flow
def example_s3_upload_flow():
    aws_credentials = AwsCredentials(
        aws_access_key_id="access_key_id",
        aws_secret_access_key="secret_access_key"
    )
    with open("../data_flows_output/2022-12-03_zillow_scrape_output.csv", "rb") as file:
        key = s3_upload(
            bucket="bucket",
            key="../data_flows_output/2022-12-03_zillow_scrape_output.csv",
            data=file.read(),
            aws_credentials=aws_credentials,
        )

example_s3_upload_flow()