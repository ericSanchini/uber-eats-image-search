import csv
import os
import requests
from googleapiclient.discovery import build
from urllib.parse import urlparse
import time
import traceback

# Google API credentials
API_KEY = 'AIzaSyAs0uaEsUrd6w9molA7ZI-4vzrvchWuNQ0'
SEARCH_ENGINE_ID = '36848e37ad1b14fda'

# File and directory paths
INPUT_FILE = r'C:\Users\erics\Downloads\wsmubereatslist.csv'
SAVE_DIRECTORY = r'C:\Users\erics\Projects\code\uber-eats-images\uber-eats-image-folder'
ERROR_LOG_FILE = 'error_log.txt'

def log_error(message):
    with open(ERROR_LOG_FILE, 'a') as f:
        f.write(f"{time.ctime()}: {message}\n")

def read_product_list(file_path):
    products = []
    try:
        print(f"Reading file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Needs Picture'].lower() == 'yes':
                    products.append(row)
        print(f"Successfully read {len(products)} products needing images")
    except Exception as e:
        error_msg = f"Error reading file {file_path}: {e}"
        print(error_msg)
        log_error(error_msg)
    return products

def create_search_client():
    try:
        print("Creating Google Custom Search client...")
        return build("customsearch", "v1", developerKey=API_KEY)
    except Exception as e:
        error_msg = f"Error creating search client: {e}"
        print(error_msg)
        log_error(error_msg)
        return None

def search_image(service, product, category):
    if not service:
        log_error("Search client is not initialized.")
        return None
    try:
        query = f"{product} {category} product image"
        print(f"Searching for image: {query}")
        result = service.cse().list(
            q=query,
            cx=SEARCH_ENGINE_ID,
            searchType='image',
            num=1,
            imgType='photo',
            fileType='jpg',
            safe='active'
        ).execute()
        if 'items' in result:
            return result['items'][0]['link']
        else:
            log_error(f"No image found for query: {query}")
    except Exception as e:
        error_msg = f"Error searching for image '{query}': {e}"
        print(error_msg)
        log_error(error_msg)
    return None

def download_image(url, file_name):
    try:
        print(f"Downloading image from: {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            file_path = os.path.join(SAVE_DIRECTORY, file_name)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Image saved to: {file_path}")
            return file_path
        else:
            log_error(f"Failed to download image. Status code: {response.status_code}")
    except Exception as e:
        error_msg = f"Error downloading image from {url}: {e}"
        print(error_msg)
        log_error(error_msg)
    return None

def process_products(products, service):
    total_products = len(products)
    for i, product in enumerate(products, 1):
        print(f"\nProcessing product {i}/{total_products}: {product['Product']}")
        try:
            image_url = search_image(service, product['Product'], product['Category'])
            print(f"Image URL: {image_url}")
            
            if image_url:
                file_extension = os.path.splitext(urlparse(image_url).path)[1] or '.jpg'
                file_name = f"{i:04d}_{product['Product'].replace(' ', '_')}{file_extension}"
                saved_path = download_image(image_url, file_name)
                if not saved_path:
                    log_error(f"Failed to save image for product: {product['Product']}")
            else:
                log_error(f"No image URL found for product: {product['Product']}")
            
            time.sleep(2)  # Delay to avoid hitting rate limits
        except Exception as e:
            error_msg = f"Error processing product {product['Product']}: {e}\n{traceback.format_exc()}"
            print(error_msg)
            log_error(error_msg)
        print("---")

if __name__ == "__main__":
    print("Script started.")

    try:
        # Ensure the save directory exists
        os.makedirs(SAVE_DIRECTORY, exist_ok=True)

        # Read the list of products
        products = read_product_list(INPUT_FILE)

        if not products:
            print("No products to process. Exiting.")
            exit(0)

        # Create the search client
        service = create_search_client()
        if service:
            # Process all products
            process_products(products, service)
        else:
            log_error("Failed to create search client. Exiting.")

    except Exception as e:
        error_msg = f"Unhandled error in main execution: {e}\n{traceback.format_exc()}"
        print(error_msg)
        log_error(error_msg)

    print("Script completed.")