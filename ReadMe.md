# 📚 Book Cover Grid Generator

This script generates a **PDF grid of book covers** by fetching images from either:

1. **A local CSV file** containing image URLs.
2. **A Google Sheet**, dynamically retrieving URLs from a specified column.

The script supports **relative paths**, filters out already processed records, and maintains a **processed list** to avoid duplication.

---

## 🛠 Installation

### **1️⃣ Install Required Packages**

Make sure you have Python **3.7+** installed. Then install the dependencies:

```bash
pip install -r rw
```

### **2️⃣ Install Additional Dependencies (Ubuntu Users)**

If you're running Ubuntu, ensure these packages are installed:

```bash
sudo apt update
sudo apt install python3-pip libjpeg-dev zlib1g-dev
```

---

## ⚙️ Usage

### **1️⃣ Run with a Local CSV File**

```bash
python generate_pdf.py --source csv --path data/urls.csv
```

- **`--source csv`** → Uses a CSV file as input.
- **`--path data/urls.csv`** → Path to the CSV file (supports **relative paths**).

**CSV Format (Columns)**:

| Column A | Column B (URL)                                                 | Column C (Status) |
| -------- | -------------------------------------------------------------- | ----------------- |
| Book 1   | [https://example.com/book1.jpg](https://example.com/book1.jpg) |                   |
| Book 2   | [https://example.com/book2.jpg](https://example.com/book2.jpg) | printed           |
| Book 3   | [https://example.com/book3.jpg](https://example.com/book3.jpg) |                   |

- **Only rows with a URL in Column B are processed.**
- **Rows where Column C is marked as "printed" are skipped.**
- **Processed URLs are moved to ****`processed.csv`**** and marked as "printed" in the original CSV.**

### **2️⃣ Run with a Google Sheet**

```bash
python main.py --source sheets --sheet-id YOUR_SHEET_ID --credentials credentials.json
```

- **`--source sheets`** → Uses Google Sheets as input.
- **`--sheet-id`** → The Google Sheets **document ID**.
- **`--credentials`** → Path to a Google Sheets API **credentials JSON file**.

#### **Google Sheets Format**

- The script reads from a sheet named **"To Process"**.
- **Column B** should contain the **image URLs**.
- **Column C** is used as a **status column** ("printed" to mark processed rows).
- After processing, rows are marked as **"printed"** in Column C and moved to a sheet named **"Processed"**.

#### **How to Get Google Sheets API Credentials**

1. Go to **Google Cloud Console** → Enable "Google Sheets API" & "Google Drive API".
2. Create a **Service Account Key (JSON format)**.
3. Share your Google Sheet **with the service account email** (read & write access).
4. Download the JSON file and provide its path as `--credentials`.

---

## 📜 Output

- **PDF File:** `book_grid.pdf`
- **Processed CSV File:** `processed.csv` (if using a local CSV file)

---

## 🚀 Features

✅ **Works with both CSV files & Google Sheets**\
✅ **Automatically downloads & resizes images**\
✅ **Prevents reprocessing by tracking processed items**\
✅ **Creates an organized A4 PDF layout**\
✅ **Supports both absolute & relative paths for CSV files**\
✅ **Google Sheets support with API authentication**

---

## 🛠 Troubleshooting

### **Common Errors & Fixes**

#### 🛑 `OSError: cannot write mode RGBA as JPEG`

✅ Solution: Convert images to RGB mode before saving (already handled in the script).

#### 🛑 `No connection adapters were found for 'data:image/gif;base64,...'`

✅ Solution: Ensure the **image selector** correctly targets a valid `<img>` tag.

#### 🛑 `Could not authenticate Google Sheets API`

✅ Solution: Verify the **credentials.json** file & make sure the **service account has access**.

#### 🛑 `FileNotFoundError: No such file or directory: 'data/urls.csv'`

✅ Solution: Ensure the CSV file exists and the path is correct.

---

## 📌 Future Enhancements

🔹 Support for other paper sizes (Letter, Legal)\
🔹 Option to add captions under each image\
🔹 Customizable image spacing & grid layout

---

## 📧 Need Help?

If you encounter any issues, feel free to open an issue or reach out! 😊

