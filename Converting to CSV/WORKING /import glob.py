import glob
import os

base_dir = "/Users/isabella/Library/Mobile Documents/com~apple~CloudDocs/Graduated/UCL EvidENT/DOWNLOADED DATA/CSV DATA/"

print("Folders under base_dir:")
print(os.listdir(base_dir))

print("\nExample files:")
for f in glob.glob(base_dir + "**/*.csv", recursive=True)[:10]:
    print(f)
