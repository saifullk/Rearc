import os
import requests
import boto3

from botocore.exceptions import NoCredentialsError
from urllib.parse import urlparse, urljoin
import hashlib

# Define the URL where the files are located
base_url = "https://download.bls.gov/pub/time.series/pr/"


headers = {
    #'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    "User-Agent": "ksaifullah@gmail.com"
}

# Define the Amazon S3 bucket and AWS credentials
bucket_name = "khalid-rearc"
aws_access_key = "KKKKKKKKKKKKKK"
aws_secret_key = "KKKKKKKKKKKKKK"
aws_region = "us-east-1"

# Initialize the S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region,
)


# Function to download and upload a file
def download_and_upload_file(file_url, bucket_name):
    try:
        # Send an HTTP GET request to the file URL

        response = requests.get(file_url, headers=headers)
        print(f"Status Code {response.status_code}")

        response.raise_for_status()

        # Get the filename from the URL
        filename = os.path.basename(urlparse(file_url).path)

        # Calculate the MD5 hash of the file content
        md5_hash = hashlib.md5(response.content).hexdigest()

        # Check if the file already exists in S3 with the same MD5 hash
        object_key = filename
        try:
            existing_object = s3.get_object(Bucket=bucket_name, Key=object_key)
            if existing_object["Metadata"].get("md5_hash") == md5_hash:
                print(f"File '{filename}' has not been updated. Skipping.")
                return
        except s3.exceptions.NoSuchKey:
            pass  # The file does not exist in S3

        # Save the downloaded file locally - This is a workaround the fact that S3 upload of response.raw
        # was uploading empty files. Needs a better solution.
        with open(object_key, "wb") as local_file:
            local_file.write(response.content)

        # Upload the file to S3
        s3.upload_file(
            object_key,
            bucket_name,
            object_key,
            ExtraArgs={"Metadata": {"md5_hash": md5_hash}, "ACL": "public-read"},
        )

        print(f"File '{filename}' uploaded to S3 bucket '{bucket_name}'")

        # Delete the local file after a successful upload
        os.remove(object_key)
        print(f"Local file deleted: {object_key}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file from URL: {e}")
    except NoCredentialsError:
        print("AWS credentials not found. Make sure to configure your AWS credentials.")


# Function to fetch and upload all files from the URL
def fetch_and_upload_all_files(base_url, bucket_name):
    try:
        # Send an HTTP GET request to the base URL
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()

        # Parse the HTML content to extract file links
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response.text, "html.parser")
        file_links = [
            urljoin(base_url, link.get("href")) for link in soup.find_all("a")
        ]

        # Iterate through the list of file links and upload/update each file in S3
        for file_link in file_links:
            if not file_link.endswith("/"):
                download_and_upload_file(file_link, bucket_name)

        # Check for deleted files in S3
        s3_objects = s3.list_objects(
            Bucket=bucket_name,
        ).get("Contents", [])
        s3_object_keys = [obj["Key"] for obj in s3_objects]
        for s3_object_key in s3_object_keys:
            file_url = urljoin(base_url, os.path.basename(s3_object_key))
            if file_url not in file_links:
                print(f"File '{s3_object_key}' has been deleted. Removing from S3.")
                s3.delete_object(Bucket=bucket_name, Key=s3_object_key)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching files from URL: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


# Fetch and upload all files from the URL to S3, handling updates and deletions
fetch_and_upload_all_files(base_url, bucket_name)
