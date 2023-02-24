""" import os

os.system(
    "sh -c \"mkdir -p '$HOME/Library/Application Support/LibreOffice/4/user/Scripts/python'\""
)
files = ["spreadsheet.py", "base.py"]
# iterate over files
for file in files:
    os.system(
        f"sh -c \"ln '{file}' '$HOME/Library/Application Support/LibreOffice/4/user/Scripts/python'\""
    )
 """
import os


os.system(
    "sh -c \"mkdir -p '$HOME/Library/Application Support/LibreOffice/4/user/Scripts/python'\""
)
os.system(
    "sh -c \"ln 'acquisitions.py' '$HOME/Library/Application Support/LibreOffice/4/user/Scripts/python'\""
)
