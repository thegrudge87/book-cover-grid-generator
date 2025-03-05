import os
import argparse
import requests
import shutil
import mimetypes
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image
from fpdf import FPDF
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# --- CONSTANTS ---
TEMP_DIR = "temp_images"
OUTPUT_PDF = "book_grid_all_in_one1.pdf"
IMAGE_SELECTOR = ".main-image-nosrc"  # CSS Selector for book cover image

# A4 paper size in mm
A4_WIDTH, A4_HEIGHT = 210, 297
MM_TO_PT = 2.834  # Convert mm to points
PAGE_WIDTH = A4_WIDTH * MM_TO_PT
PAGE_HEIGHT = A4_HEIGHT * MM_TO_PT

# Book cover size in mm
COVER_WIDTH_MM = 30
COVER_HEIGHT_MM = 43
COVER_WIDTH_PT = int(COVER_WIDTH_MM * MM_TO_PT)
COVER_HEIGHT_PT = int(COVER_HEIGHT_MM * MM_TO_PT)

# Margins and Spacing
MARGIN_LEFT_MM = 9
MARGIN_TOP_MM = 9
SPACING_MM = 2
MARGIN_LEFT_PT = MARGIN_LEFT_MM * MM_TO_PT
MARGIN_TOP_PT = MARGIN_TOP_MM * MM_TO_PT
SPACING_PT = SPACING_MM * MM_TO_PT

# Calculate max images per row and column
cols = int((PAGE_WIDTH - 2 * MARGIN_LEFT_PT) // (COVER_WIDTH_PT + SPACING_PT))
rows = int((PAGE_HEIGHT - 2 * MARGIN_TOP_PT) // (COVER_HEIGHT_PT + SPACING_PT))
images_per_page = cols * rows

# Create temp folder
os.makedirs(TEMP_DIR, exist_ok=True)

def is_image_url(url):
    """Checks if a URL is an image by looking at its content type."""
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "").lower()
            return content_type.startswith("image")
        return False
    except Exception as e:
        print(f"⚠️ Could not check URL type for {url}: {e}")
        return False

def fetch_image_url(page_url):
    """
    Extract the actual image URL from an HTML page or return the URL directly if it's already an image.

    - If the URL points to an image, return it directly.
    - If it's an HTML page, look for an image using the predefined CSS selector.
    """
    if is_image_url(page_url):
        return page_url  # It's already an image

    try:
        response = requests.get(page_url, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Skipping {page_url} (Failed to load page)")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        img_tag = soup.select_one(IMAGE_SELECTOR)
        if img_tag and img_tag.get("data-src"):
            return img_tag["data-src"]
        else:
            print(f"⚠️ No image found at {page_url}")
            return None
    except Exception as e:
        print(f"❌ Error fetching image from {page_url}: {e}")
        return None

def process_images(url_list):
    """
    Process the given list of image URLs, generate a grid layout PDF, and save it.

    - Downloads each image, resizes it, and places it in a structured layout on A4-sized pages.
    - Each page contains a fixed number of images (calculated dynamically).
    - Saves the processed URLs in a list for updating the data source.
    """
    pdf = FPDF(unit="mm", format="A4")
    processed_urls = []

    for i in range(0, len(url_list), images_per_page):
        pdf.add_page()
        page_urls = url_list[i:i + images_per_page]

        for index, page_url in enumerate(page_urls):
            try:
                # Get image URL
                img_url = fetch_image_url(page_url)
                if not img_url:
                    continue  # Skip if no image found

                # Download the image
                img_name = f"{i + index + 1}.jpg"
                img_path = os.path.join(TEMP_DIR, img_name)
                response = requests.get(img_url, stream=True, timeout=10)
                if response.status_code == 200:
                    with open(img_path, "wb") as file:
                        file.write(response.content)
                else:
                    print(f"⚠️ Skipping {img_url} (Failed to Download)")
                    continue

                # Open and process image
                img = Image.open(img_path)
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                img = img.resize((COVER_WIDTH_PT * 2, COVER_HEIGHT_PT * 2), Image.LANCZOS)

                # Compute X and Y positions
                col = index % cols
                row = index // cols
                x_offset = MARGIN_LEFT_MM + col * (COVER_WIDTH_MM + SPACING_MM)
                y_offset = MARGIN_TOP_MM + row * (COVER_HEIGHT_MM + SPACING_MM)

                # Save high-quality resized image
                img.save(img_path, quality=95, optimize=True)

                # Add to PDF
                pdf.image(img_path, x=x_offset, y=y_offset, w=COVER_WIDTH_MM, h=COVER_HEIGHT_MM)
                print(f"processed {i + index + 1}/{len(url_list)}")

                # Store processed URL
                processed_urls.append([page_url])

            except Exception as e:
                print(f"❌ Error processing {page_url}: {e}")

    # Save the final PDF
    pdf.output(OUTPUT_PDF)
    print(f"✅ PDF saved as {OUTPUT_PDF}")

    # Cleanup temp images
    shutil.rmtree(TEMP_DIR)
    print(f"✅ Processed images removed.")

    return processed_urls

def process_google_sheets(sheet_id, credentials_file):
    """
    Read URLs from a Google Sheet, process images, and update the sheet by moving processed URLs to another sheet.

    - Reads from the "To Process" sheet.
    - Moves successfully processed URLs to the "Processed" sheet.
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(sheet_id)
    source_sheet = sheet.worksheet("To Process")
    processed_sheet = sheet.worksheet("Processed")

    # Get all data from the sheet
    data = source_sheet.get_all_values()

    # Extract rows where Column B is NOT empty and Column C is NOT "printed"
    url_list = [row[1] for row in data[1:] if row[1].strip() and row[2].strip().lower() != "printed"]
    #url_list = source_sheet.col_values(2)[1:]  # Read from Column B instead of Column A (excluding header --> [1:])

    processed_urls = process_images(url_list)

    if processed_urls:
        # Append processed URLs to "Processed" sheet
        processed_sheet.append_rows(processed_urls)

        # Mark processed rows as "printed"
        for i, row in enumerate(data[1:], start=2):  # Start from row 2 (skip headers)
            if row[1] in processed_urls:
                source_sheet.update_cell(i, 3, "printed")  # Column C gets "printed"

    print(f"✅ Processed URLs moved to 'Processed' tab.")

def process_csv_file(csv_path):
    """Fetches URLs from a CSV file and updates it after processing."""

    # Convert to absolute path
    csv_path = os.path.abspath(csv_path)

    # Read CSV
    df = pd.read_csv(csv_path)

    if "url" not in df.columns:
        print("❌ CSV file must have a 'url' column.")
        return

    url_list = df["url"].tolist()
    processed_urls = process_images(url_list)

    if processed_urls:
        processed_df = pd.DataFrame(processed_urls, columns=["url"])
        processed_df.to_csv("processed.csv", index=False)
        df = df[~df["url"].isin(processed_df["url"])]
        df.to_csv(csv_path, index=False)

    print(f"✅ Processed URLs moved to 'processed.csv'.")

    # Cleanup temp images
    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a book cover PDF grid from URLs in a CSV file or Google Sheet.")
    parser.add_argument("--source", choices=["csv", "sheets"], required=True, help="Specify data source: 'csv' or 'sheets'")
    parser.add_argument("--path", help="Path to local CSV file (if source is 'csv')")
    parser.add_argument("--sheet-id", help="Google Sheet ID (if source is 'sheets')")
    parser.add_argument("--credentials", help="Path to Google Sheets API credentials JSON (if source is 'sheets')")

    args = parser.parse_args()

    if args.source == "csv":
        if not args.path:
            print("❌ CSV file path is required.")
        else:
            process_csv_file(args.path)
    elif args.source == "sheets":
        if not args.sheet_id or not args.credentials:
            print("❌ Google Sheet ID and credentials file are required.")
        else:
            process_google_sheets(args.sheet_id, args.credentials)
