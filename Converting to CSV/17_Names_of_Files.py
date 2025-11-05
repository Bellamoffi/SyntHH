import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import pyreadstat
import zipfile
from ftplib import FTP
import pandas as pd
import re

def sanitize_filename(name):
    """
    Replace any character that's not alphanumeric, dash, or underscore with underscore.
    Collapse multiple underscores into one and strip leading/trailing underscores.
    """
    sanitized = re.sub(r'[^A-Za-z0-9_-]+', '_', name)
    sanitized = re.sub(r'_+', '_', sanitized)  # collapse multiple underscores
    return sanitized.strip('_')

def download_and_convert_all_nhanes(base_url, xpt_base_folder, csv_base_folder, readable_base_folder, datasets=None):
    """
    Downloads NHANES datasets (XPT/ZIP/FTP), converts XPT to CSV,
    creates human-readable CSVs with 'CODE - Label' headers (uppercase codes),
    and saves a mapping file for each dataset.
    Renames CSV files to include year range and dataset name safely.
    """

    os.makedirs(xpt_base_folder, exist_ok=True)
    os.makedirs(csv_base_folder, exist_ok=True)
    os.makedirs(readable_base_folder, exist_ok=True)

    print(f"Fetching NHANES page from {base_url}...")
    resp = requests.get(base_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if table is None:
        print("❌ No table found on the page.")
        return

    rows = table.find_all("tr")
    header = [th.get_text(strip=True) for th in rows[0].find_all("th")]
    year_idx = header.index("Years")
    data_name_idx = header.index("Data File Name")
    data_file_idx = header.index("Data File")
    doc_file_idx = header.index("Doc File")
    print(f"Detected columns: {header}")

    def download_file(url, save_path):
        parsed = urlparse(url)
        if parsed.scheme == "ftp":
            print(f"Downloading FTP file: {os.path.basename(save_path)}")
            ftp = FTP(parsed.hostname)
            ftp.login()
            ftp.cwd(os.path.dirname(parsed.path))
            with open(save_path, "wb") as f:
                ftp.retrbinary(f"RETR {os.path.basename(parsed.path)}", f.write)
            ftp.quit()
        else:
            print(f"Downloading: {os.path.basename(save_path)}")
            r = requests.get(url, stream=True)
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    def convert_xpt_to_csv(xpt_path, csv_path):
        try:
            df, meta = pyreadstat.read_xport(xpt_path)
            try:
                df.to_csv(csv_path, index=False, encoding="utf-8")
            except UnicodeEncodeError:
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"✅ Converted to CSV: {os.path.basename(csv_path)}")
            return df
        except Exception as e:
            print(f"❌ Failed to convert {os.path.basename(xpt_path)}: {e}")
            return None

    def parse_doc_page(doc_url):
        try:
            r = requests.get(doc_url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            mapping = {}
            var_titles = soup.find_all("h3", class_="vartitle")
            for h3 in var_titles:
                text = h3.get_text(strip=True)
                if " - " in text:
                    var, desc = text.split(" - ", 1)
                    var_upper = var.strip().upper()
                    mapping[var_upper] = f"{var_upper} - {desc.strip()}"
            return mapping
        except Exception as e:
            print(f"⚠️ Failed to parse doc page {doc_url}: {e}")
            return {}

    for row in rows[1:]:
        cols = row.find_all("td")
        if not cols:
            continue

        dataset_name = cols[data_name_idx].get_text(strip=True)
        dataset_years = cols[year_idx].get_text(strip=True)
        if not dataset_name:
            continue

        if datasets and dataset_name not in datasets:
            continue

        print(f"\n🔍 Processing dataset: {dataset_name} ({dataset_years})")

        xpt_folder = os.path.join(xpt_base_folder, dataset_name)
        csv_folder = os.path.join(csv_base_folder, dataset_name)
        readable_folder = os.path.join(readable_base_folder, dataset_name)
        os.makedirs(xpt_folder, exist_ok=True)
        os.makedirs(csv_folder, exist_ok=True)
        os.makedirs(readable_folder, exist_ok=True)

        doc_links = cols[doc_file_idx].find_all("a")
        mapping = {}
        if doc_links:
            doc_url = urljoin(base_url, doc_links[0].get("href"))
            mapping = parse_doc_page(doc_url)
            if mapping:
                map_df = pd.DataFrame(list(mapping.items()), columns=["Code", "Label"])
                map_path = os.path.join(readable_folder, "mapping.csv")
                map_df.to_csv(map_path, index=False, encoding="utf-8-sig")
                print(f"📝 Saved mapping file: {map_path}")

        links = cols[data_file_idx].find_all("a")
        for link in links:
            href = link.get("href")
            if not href:
                continue

            original_file_name = os.path.basename(href)
            base_name = os.path.splitext(original_file_name)[0]

            # SANITIZED FILE NAMES
            dataset_name_sanitized = sanitize_filename(dataset_name)
            dataset_years_sanitized = sanitize_filename(dataset_years)
            new_base_name = f"{dataset_years_sanitized}_{dataset_name_sanitized}_{base_name}"

            xpt_path = os.path.join(xpt_folder, original_file_name)
            csv_path = os.path.join(csv_folder, f"{new_base_name}.csv")
            readable_path = os.path.join(readable_folder, f"{new_base_name}_readable.csv")

            if not os.path.exists(xpt_path):
                download_file(urljoin(base_url, href), xpt_path)
            else:
                print(f"Already downloaded: {original_file_name}")

            # Handle ZIP files
            if xpt_path.lower().endswith(".zip"):
                with zipfile.ZipFile(xpt_path, 'r') as zip_ref:
                    zip_ref.extractall(xpt_folder)
                    for extracted_file in zip_ref.namelist():
                        if extracted_file.lower().endswith(".xpt"):
                            extracted_base = os.path.splitext(extracted_file)[0]
                            sanitized_extracted_base = sanitize_filename(extracted_base)
                            df = convert_xpt_to_csv(
                                os.path.join(xpt_folder, extracted_file),
                                os.path.join(csv_folder, f"{dataset_years_sanitized}_{dataset_name_sanitized}_{sanitized_extracted_base}.csv")
                            )
                            if df is not None and mapping:
                                df_renamed = df.rename(columns=lambda c: mapping.get(c.upper(), c))
                                df_renamed.to_csv(
                                    os.path.join(readable_folder, f"{dataset_years_sanitized}_{dataset_name_sanitized}_{sanitized_extracted_base}_readable.csv"),
                                    index=False, encoding="utf-8-sig"
                                )
                                print(f"📑 Saved readable CSV for {extracted_file}")

            # Handle regular XPT files
            elif xpt_path.lower().endswith(".xpt"):
                if not os.path.exists(csv_path):
                    df = convert_xpt_to_csv(xpt_path, csv_path)
                else:
                    print(f"CSV already exists: {os.path.basename(csv_path)}")
                    df = pd.read_csv(csv_path)

                if df is not None and mapping:
                    df_renamed = df.rename(columns=lambda c: mapping.get(c.upper(), c))
                    df_renamed.to_csv(readable_path, index=False, encoding="utf-8-sig")
                    print(f"📑 Saved readable CSV: {os.path.basename(readable_path)}")

    print("\n🎉 All datasets processed (with readable versions, mapping files, and uppercase codes)!")

# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    download_and_convert_all_nhanes(
        base_url="https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Examination",
        xpt_base_folder="/Users/isabella/Library/Mobile Documents/com~apple~CloudDocs/Graduated/UCL EvidENT/DOWNLOADED DATA/XPT DATA",
        csv_base_folder="/Users/isabella/Library/Mobile Documents/com~apple~CloudDocs/Graduated/UCL EvidENT/DOWNLOADED DATA/CSV DATA",
        readable_base_folder="/Users/isabella/Library/Mobile Documents/com~apple~CloudDocs/Graduated/UCL EvidENT/DOWNLOADED DATA/CSV READABLE",
        datasets=[
            "Blood Pressure",
            "Balance"
        ]
    )
