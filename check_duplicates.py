
from pathlib import Path
import pandas as pd

file_path = Path("data/processed/soc_cleaned.csv")

if not file_path.exists():
    print("Dataset not found:", file_path)
    raise SystemExit(1)

print("Reading dataset in batches...")

total_rows = 0
duplicate_rows_in_batches = 0
label_counts = {}

try:
    for chunk in pd.read_csv(
        file_path,
        chunksize=2000,
        low_memory=True,
    ):
        chunk.columns = chunk.columns.str.strip()
        total_rows += len(chunk)

        label_column = next(
            (
                col for col in ["Label", "Class", "Target"]
                if col in chunk.columns
            ),
            None,
        )

        if label_column is None:
            print("Error: Label, Class, or Target column not found.")
            raise SystemExit(1)

        duplicate_rows_in_batches += int(
            chunk.duplicated().sum()
        )

        counts = chunk[label_column].value_counts()

        for label, count in counts.items():
            label = str(label)
            label_counts[label] = (
                label_counts.get(label, 0) + int(count)
            )

    print("\nDataset check completed successfully.")
    print("Total rows:", total_rows)
    print(
        "Duplicate rows within batches:",
        duplicate_rows_in_batches,
    )

    print("\nClass distribution:")
    for label, count in label_counts.items():
        print(f"{label}: {count}")

    print(
        "\nNote: duplicates occurring across different batches "
        "are not included in the duplicate count."
    )

except Exception as exc:
    print("\nDataset check failed:", repr(exc))
