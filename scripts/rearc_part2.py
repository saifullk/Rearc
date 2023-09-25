import requests
import boto3
from botocore.exceptions import NoCredentialsError
import json

# Define the API URL
api_url = "https://datausa.io/api/data?drilldowns=Nation&measures=Population"

# Define your AWS S3 bucket and object key
s3_bucket_name = "khalid-rearc2"
s3_object_key = "population.json"
aws_access_key = "KKKKKKKKKKKKKK"
aws_secret_key = "KKKKKKKKKKKKKK"
aws_region = "us-east-1"

try:
    # Make a GET request to the API
    response = requests.get(api_url)

    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Initialize the S3 client
        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
        )

        # Upload the data as JSON to S3
        s3.put_object(
            Bucket=s3_bucket_name,
            Key=s3_object_key,
            Body=json.dumps(data),
            ContentType="application/json",
        )

        print(f"Data uploaded to S3: s3://{s3_bucket_name}/{s3_object_key}")
    else:
        print(f"Failed to fetch data from the API. Status code: {response.status_code}")

except NoCredentialsError:
    print("AWS credentials not found. Please configure your AWS credentials.")
except Exception as e:
    print(f"An error occurred: {e}")
