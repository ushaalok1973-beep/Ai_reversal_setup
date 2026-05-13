import os
import pandas as pd

# 👇 THIS IS THE "TOP" (VERY FIRST EXECUTION PART)
print("🔥 SCANNER STARTED")

print("WORKING DIR:", os.getcwd())
print("FILES HERE:", os.listdir())

file_path = os.path.join(os.getcwd(), "ind_niftymidcap150list.csv")

print("LOOKING FOR CSV:", file_path)

if not os.path.exists(file_path):
    raise Exception("❌ CSV NOT FOUND IN GITHUB ROOT")

df_midcap = pd.read_csv(file_path)

print("CSV LOADED OK")
print("ROWS:", len(df_midcap))
print("COLUMNS:", df_midcap.columns)

# 👇 ONLY AFTER THIS, KEEP YOUR ORIGINAL CODE BELOW
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
