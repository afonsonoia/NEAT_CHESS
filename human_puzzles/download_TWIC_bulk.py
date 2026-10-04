import urllib.request
import time
import os

# 1. Configuration
START_NUMBER = 920
END_NUMBER = 1637
DESTINATION_FOLDER = r"D:\downloads"

os.makedirs(DESTINATION_FOLDER, exist_ok=True)

print(f"Starting download of TWIC files from {START_NUMBER} to {END_NUMBER}...\n")

# Browser headers for TWIC server
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

for number in range(START_NUMBER, END_NUMBER + 1):
    url = f"https://theweekinchess.com/zips/twic{number}g.zip"
    file_name = f"twic{number}g.zip"
    full_path = os.path.join(DESTINATION_FOLDER, file_name)

    print(f"Downloading {file_name}...", end=" ", flush=True)

    try:
        # Create request with headers
        req = urllib.request.Request(url, headers=headers)

        # Open connection and save file
        with urllib.request.urlopen(req) as response:
            with open(full_path, 'wb') as out_file:
                out_file.write(response.read())

        print("OK!")

    except urllib.error.HTTPError as e:
        print(f"FAILED! (Error {e.code} - Site rejected request or file does not exist)")
    except Exception as e:
        print(f"FAILED! Error: {e}")

    time.sleep(3)

print("\nAll downloads finished!")