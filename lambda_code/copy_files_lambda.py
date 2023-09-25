import os
import requests
import boto3

from botocore.exceptions import NoCredentialsError
import hashlib
from urllib.parse import urljoin


# This lambda gets all files on BLS web site and copies them to an AWS S3 Bucket for analysis

# request header to be able to call and end point

headers = {"User-Agent": "ksaifullah@gmail.com"}


def copy_files_to_s3(event, context):
    source_url = os.environ["SOURCE_URL"]
    destination_bucket = os.environ["DESTINATION_BUCKET"]

    # List files in the destination S3 bucket
    s3 = boto3.client("s3")
    existing_files = set()

    try:
        response = s3.list_objects_v2(Bucket=destination_bucket)
        if "Contents" in response:
            for obj in response["Contents"]:
                existing_files.add(obj["Key"])
    except Exception as e:
        return {"statusCode": 500, "body": f"Error listing S3 objects: {str(e)}"}

    # Get a list of files from the source URL
    try:
        response = requests.get(source_url, headers=headers)
        if response.status_code == 200:
            # Parse the HTML content to extract file links
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "html.parser")
            file_links = [
                urljoin(source_url, link.get("href")) for link in soup.find_all("a")
            ]
        else:
            return {
                "statusCode": 500,
                "body": "Failed to fetch file list from source URL",
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error fetching file list from source URL: {str(e)}",
        }

    # Copy files that have changed or are new
    for source_file_url in file_links:
        # ignore href links that are not actual files
        if source_file_url.endswith("/"):
            continue
        # to get actual file name
        file_name = source_file_url.split("/")[-1]

        # Check if the file is in the list of existing files
        if file_name not in existing_files:
            copy_file(source_file_url, file_name, destination_bucket, s3)
        else:
            # Compare content hashes to check for changes
            existing_file_hash = get_s3_object_hash(destination_bucket, file_name, s3)
            new_file_hash = get_url_content_hash(source_file_url)

            if existing_file_hash != new_file_hash:
                copy_file(source_file_url, file_name, destination_bucket, s3)

    # Delete files that have been removed at the source
    for existing_file in existing_files:
        file_url = urljoin(source_url, os.path.basename(existing_file))
        if file_url not in file_links:
            s3.delete_object(Bucket=destination_bucket, Key=existing_file)

    return {
        "statusCode": 200,
        "body": "Files copied to S3 and outdated files deleted successfully",
    }


def get_url_content_hash(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.content
        return hashlib.md5(content).hexdigest()
    else:
        return None


def get_s3_object_hash(bucket, key, s3):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read()
        return hashlib.md5(content).hexdigest()
    except Exception as e:
        return None


def copy_file(source_url, file_name, destination_bucket, s3):
    try:
        response = requests.get(source_url, headers=headers)
        if response.status_code == 200:
            s3.put_object(
                Bucket=destination_bucket, Key=file_name, Body=response.content
            )
        else:
            print(f"Failed to copy file '{file_name}' from source URL")
    except Exception as e:
        print(f"Error copying file '{file_name}' from source URL: {str(e)}")


if __name__ == "__main__":
    # For local testing
    event = {}
    context = {}
    result = copy_files_to_s3(event, context)
    print(result)
