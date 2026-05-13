import os

print("=== SCRIPT STARTED ===")

file_path = os.path.join(os.getcwd(), "ind_niftymidcap150list.csv")

print("WORKING DIRECTORY:", os.getcwd())
print("LOOKING FOR FILE:", file_path)
print("FILE EXISTS:", os.path.exists(file_path))

if not os.path.exists(file_path):
    raise Exception("❌ CSV FILE NOT FOUND IN GITHUB REPO ROOT")

try:
    df = pd.read_csv(file_path)
    print("CSV LOADED SUCCESSFULLY")
    print("ROWS:", len(df))
    print("COLUMNS:", df.columns)

except Exception as e:
    print("CSV READ ERROR:", e)
    raise e
