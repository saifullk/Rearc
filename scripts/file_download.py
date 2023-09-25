import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# URL of the BLS time series Data
url = "https://download.bls.gov/pub/time.series/pr/"

headers = {
    #'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    "User-Agent": "ksaifullah@gmail.com"
}

# Local directory where you want to save the downloaded files
local_directory = "downloaded_files"  # Replace with your desired directory path

# Create the local directory if it doesn't exist
os.makedirs(local_directory, exist_ok=True)

try:
    # Send an HTTP GET request to the URL
    response = requests.get(url, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all <a> tags with href attributes (links)
        links = soup.find_all("a", href=True)

        # Get a list of all local files
        local_files = os.listdir(local_directory)

        # Iterate through the local files
        for local_file in local_files:
            local_file_path = os.path.join(local_directory, local_file)

            # Check if the local file is not present on the source URL
            file_exists_on_url = any(
                urljoin(url, link["href"]) == urljoin(url, local_file) for link in links
            )

            if not file_exists_on_url:
                # Delete the local file if it's not present at the source URL
                os.remove(local_file_path)
                print(f"Deleted: {local_file_path}")

        # Iterate through the links
        for link in links:
            file_url = urljoin(url, link["href"])  # Construct the absolute URL
            if file_url.endswith("/"):
                continue
            file_name = os.path.join(local_directory, os.path.basename(file_url))

            # Check if the file exists locally
            if os.path.exists(file_name):
                # Get the last modified timestamp of the local file
                local_file_timestamp = os.path.getmtime(file_name)

                # Get the last modified timestamp of the remote file
                headers = requests.head(file_url).headers
                remote_file_timestamp = headers.get("Last-Modified")

                if remote_file_timestamp and (
                    os.path.getmtime(file_name)
                    < requests.utils.parsedate(remote_file_timestamp)
                ):
                    # Download and replace the local file if the remote file is newer
                    file_response = requests.get(file_url, headers=headers)
                    if file_response.status_code == 200:
                        with open(file_name, "wb") as file:
                            file.write(file_response.content)
                        print(f"Updated: {file_name}")
                    else:
                        print(f"Failed to download: {file_url}")
                else:
                    print(f"Skipping: {file_name} (up to date)")
            else:
                # Download the file if it doesn't exist locally
                file_response = requests.get(file_url, headers=headers)
                if file_response.status_code == 200:
                    with open(file_name, "wb") as file:
                        file.write(file_response.content)
                    print(f"Downloaded: {file_name}")
                else:
                    print(f"Failed to download: {file_url}")

    else:
        print(f"Failed to fetch the page. Status code: {response.status_code}")

except Exception as e:
    print(f"An error occurred: {e}")
