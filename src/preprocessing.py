
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/MachineLearningCSV")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "soc_cleaned.csv"

def load_dataset():
    csv_files = sorted(DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {DATA_DIR.resolve()}. "
            "Check your dataset folder."
        )

    frames = []

    
    for file in csv_files:
        # Keep Tuesday data separate for independent testing.
        if "tuesday" in file.name.lower():
            print(f"Holding out for testing: {file.name}")
            continue

        print(f"Reading: {file.name}")

        df = pd.read_csv(file, low_memory=False)

        df.columns = df.columns.str.strip()

        # Find the target label column
        label_col = next(
            (
                col for col in df.columns
                if col.strip().lower() in ("label", "class")
            ),
            None
        )

        if label_col is None:
            print(f"Skipping {file.name}: no label/class column found.")
            continue

        df = df.rename(columns={label_col: "Label"})
        frames.append(df)

    if not frames:
        raise ValueError(
            "No usable CSV files with a Label or Class column were found."
        )

    return pd.concat(frames, ignore_index=True)

def main():
    df = load_dataset()

    # Normalize column names and label text
    df.columns = df.columns.str.strip()
    df["Label"] = df["Label"].astype("string").str.strip()

    # Remove invalid and duplicate rows
    df = df.dropna(subset=["Label"])
    df = df.drop_duplicates()

    # Convert feature columns to numeric where possible
    feature_cols = [col for col in df.columns if col != "Label"]

    for col in feature_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Replace infinite values and remove rows with invalid features
    df[feature_cols] = df[feature_cols].replace(
        [float("inf"), float("-inf")], float("nan")
    )
    df = df.dropna(subset=feature_cols)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print("\nDataset preprocessing completed.")
    print("Saved to:", OUTPUT_FILE.resolve())
    print("Rows:", len(df))
    print("Features:", len(feature_cols))
    print("\nLabel distribution:")
    print(df["Label"].value_counts().to_string())

if __name__ == "__main__":
    main()
