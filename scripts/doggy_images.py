import requests
import sqlite3
import json
import boto3
from botocore.exceptions import NoCredentialsError


# Connect to the SQLite in-memory database
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

# Create a table to store the data
cursor.execute(
    """CREATE TABLE dogs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   breed TEXT,
                   image_url TEXT
                )"""
)

# Fetch data from the Dog API
url = "https://dog.ceo/api/breeds/list/all"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    # "User-Agent": "ksaifullah@gmail.com",
}

response = requests.get(url, headers=headers)
data = response.json()


# Insert data into the database
for breed, sub_breeds in data["message"].items():
    if len(sub_breeds) == 0:
        cursor.execute("INSERT INTO dogs (breed, image_url) VALUES (?, ?)", (breed, ""))
    else:
        for sub_breed in sub_breeds:
            cursor.execute(
                "INSERT INTO dogs (breed, image_url) VALUES (?, ?)",
                (f"{sub_breed} {breed}", ""),
            )


# Update the database with image URLs
cursor.execute("SELECT id, breed FROM dogs")
breed_data = cursor.fetchall()
for row in breed_data:
    id, breed = row
    image_url = f"https://dog.ceo/api/breed/{breed}/images/random"
    response = requests.get(image_url)
    data = response.json()
    image_url = data["message"]

    cursor.execute("UPDATE dogs SET image_url = ? WHERE id = ?", (image_url, id))

    # Fetch all data from the database
cursor.execute("SELECT * FROM dogs")
dog_data = cursor.fetchall()

# Create a list of dictionaries for JSON conversion
dog_list = []
for row in dog_data:
    id, breed, image_url = row
    dog_list.append({"id": id, "breed": breed, "image_url": image_url})


# Output the data as a JSON file
with open("dog_data.json", "w") as json_file:
    json.dump(dog_list, json_file, indent=2)


# Define the Amazon S3 bucket and AWS credentials
bucket_name = "khalid-datalogz"
aws_access_key = "AKIAZLFUDZDJUDV6UF3K"
aws_secret_key = "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"
aws_region = "us-east-1"
object_name = "dog_data.json"

# Initialize the S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region,
)

s3 = boto3.client(
    "s3", aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key
)


try:
    s3.upload_file(
        "dog_data.json",
        bucket_name,
        object_name,
        ExtraArgs={"ACL": "public-read"},
    )
    print(f"Uploaded 'dog_data.json' to '{bucket_name}/{object_name}'")
except NoCredentialsError:
    print("AWS credentials not available. Make sure to configure your AWS credentials.")
