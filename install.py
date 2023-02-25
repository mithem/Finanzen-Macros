import os

os.system("sh -c \"mkdir -p '$HOME/Library/Application Support/LibreOffice/4/user/Scripts/python'\"")

files = ["acquisitions.py", "set_simulation_date.py"]

for file in files:
    os.system(f"sh -c \"ln '{file}' '$HOME/Library/Application Support/LibreOffice/4/user/Scripts/python'\"")
