
from pathlib import Path
import pandas as pd

file_path = Path("data/processed/soc_cleaned.csv")

if not file_path.exists():
    print("Dataset not found:", file_path)
    raise SystemExit(1)

label_counts = {}

print("Counting labels in batches...")

for chunk in pd.read_csv(
    file_path,
    chunksize=20000,
    low_memory=True,
):
    chunk.columns = chunk.columns.str.strip()

    label_column = next(
        (
            col for col in ["Label", "Class", "Target"]
            if col in chunk.columns
        ),
        None,
    )

    if label_column is None:
        print("Label column not found.")
        raise SystemExit(1)

    counts = chunk[label_column].value_counts()

    for label, count in counts.items():
        label = str(label).strip()
        label_counts[label] = (
            label_counts.get(label, 0) + int(count)
        )

total = sum(label_counts.values())

print("\nClass Distribution")
for label, count in sorted(label_counts.items()):
    percentage = count / total * 100
    print(f"{label}: {count:,} ({percentage:.2f}%)")

print(f"\nTotal records: {total:,}")
