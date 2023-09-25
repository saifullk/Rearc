import os
import requests
import boto3

headers = {"User-Agent": "ksaifullah@gmail.com"}

# This lambda calls an API and and gets the JSON output and saves it to an AWS S3 Bucket


def call_api_and_save_to_s3(event, context):
    api_url = source_url = os.environ["SOURCE_URL"]
    output_bucket = os.environ["OUTPUT_BUCKET"]
    output_file = os.environ["OUTPUT_FILE"]

    # Call the API
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        # Save JSON response to S3 bucket
        s3 = boto3.client("s3")
        s3.put_object(Bucket=output_bucket, Key=output_file, Body=response.text)
        return {"statusCode": 200, "body": "API data saved to S3 successfully"}
    else:
        return {"statusCode": 500, "body": "Failed to call API and save data to S3"}


if __name__ == "__main__":
    # For local testing
    event = {}
    context = {}
    result = call_api_and_save_to_s3(event, context)
    print(result)
