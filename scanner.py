import os

print("STARTING SCRIPT")

file_path = os.path.join(os.getcwd(), "ind_niftymidcap150list.csv")

print("LOOKING FOR FILE:", file_path)
print("FILE EXISTS?", os.path.exists(file_path))

if not os.path.exists(file_path):
    raise Exception("CSV FILE NOT FOUND IN REPO ROOT!")

df = pd.read_csv(file_path)

print("CSV LOADED SUCCESSFULLY")
print("COLUMNS:", df.columns)
print("ROWS:", len(df))
