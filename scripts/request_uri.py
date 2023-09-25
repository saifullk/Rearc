import requests
from bs4 import BeautifulSoup
import os

# URL of the directory containing the files
base_url = "https://download.bls.gov/pub/time.series/pr"

try:
    # Send an HTTP GET request to the URL
    response = requests.get(base_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all links (href) on the page
        links = soup.find_all("a")

        # Loop through the links and download each file
        for link in links:
            file_url = base_url + "/" + link.get("href")
            # Exclude links to directories and parent directories (..)
            if not link.get("href").endswith("/"):
                file_name = link.get("href").split("/")[-1]
                print(f"Downloading {file_name}...")
                file_response = requests.get(file_url)

                if file_response.status_code == 200:
                    # Save the file to the current working directory
                    with open(file_name, "wb") as file:
                        file.write(file_response.content)
                    print(f"Downloaded {file_name}")
                else:
                    print(f"Failed to download {file_name}. Status code: {file_response.status_code}")

    else:
        print(f"Failed to access the URL. Status code: {response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")