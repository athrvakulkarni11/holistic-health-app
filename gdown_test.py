import gdown
import zipfile
import pandas as pd
import os

def download_and_extract():
    # File ID from the shared link
    file_id = "1ITz-4jaXpk_72PJKTyLt_YXIafXmEkAF"
    
    # Construct the direct download URL
    file_url = f"https://drive.google.com/uc?id={file_id}"
    
    # Output filename
    zip_file = "takeout-20250222T085926Z-001.zip"
    
    # Download the file if it doesn't exist
    if not os.path.exists(zip_file):
        gdown.download(file_url, zip_file, quiet=False)
        print("Download complete!")
    
    # Extract the zip file
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall('.')
    print("Extraction complete!")
    
    # Path to the CSV file
    csv_path = os.path.join('Takeout', 'Fit', 'Daily activity metrics', 'Daily activity metrics.csv')
    
    # Read and display the CSV
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print("\nFirst few rows of the CSV file:")
        print(df.head())
        return df
    else:
        print(f"Error: Could not find CSV file at {csv_path}")
        return None

if __name__ == "__main__":
    df = download_and_extract()
    if df is not None:
        # Display basic information about the dataset
        print("\nDataset Info:")
        print(df.info())
        
        print("\nBasic Statistics:")
        print(df.describe())
