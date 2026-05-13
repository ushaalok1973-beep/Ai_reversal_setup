import os
import pandas as pd

print("=== SCRIPT START STARTED ===")

try:
    file_name = "ind_niftymidcap150list.csv"

    print("Looking for file in:", os.getcwd())
    print("Files in directory:", os.listdir())

    if not os.path.exists(file_name):
        raise Exception("CSV NOT FOUND IN ROOT DIRECTORY")

    df = pd.read_csv(file_name)

    print("CSV LOADED SUCCESSFULLY")
    print("Rows:", len(df))
    print("Columns:", df.columns)

    print("TEST PASSED — SCRIPT IS WORKING")

except Exception as e:
    print("❌ ERROR OCCURRED:")
    print(e)

    # FORCE SHOW FAILURE REASON
    raise
