
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/MachineLearningCSV")

csv_files = sorted(DATA_DIR.glob("*.csv"))

if not csv_files:
    print("No CSV files found.")
    print("Check the dataset folder path:", DATA_DIR.resolve())
else:
    print(f"Found {len(csv_files)} CSV files.")

    for file in csv_files:
        print("\n" + "=" * 60)
        print("FILE:", file.name)

        try:
            df = pd.read_csv(file, nrows=5, low_memory=False)
            print("Columns:", len(df.columns))
            print("Column names:")
            print(df.columns.tolist())

            label_columns = [
                col for col in df.columns
                if col.strip().lower() in ("label", "class")
            ]

            for col in label_columns:
                print(f"\nLabels in '{col}':")
                print(df[col].value_counts(dropna=False))

        except Exception as error:
            print("Could not read this file:", error)
