
from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

DATA_FILE = Path("data/processed/soc_cleaned.csv")
MODEL_DIR = Path("models")
REPORT_DIR = Path("reports")

# Limit training size to reduce memory and training time.
MAX_ROWS = 100_000
RANDOM_STATE = 42


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}. "
            "Run python src/preprocessing.py first."
        )

    print("Loading cleaned dataset...")
    df = pd.read_csv(DATA_FILE, low_memory=False)
    df.columns = df.columns.str.strip()

    if "Label" not in df.columns:
        raise ValueError("The cleaned dataset has no Label column.")

    df["Label"] = df["Label"].astype(str).str.strip()
    df = df.dropna(subset=["Label"])

    # Convert labels to a binary target:
    # BENIGN = 0, any other label = 1 (attack).
    df["Target"] = (
        df["Label"].str.upper() != "BENIGN"
    ).astype(int)

    # Use numeric traffic features only.
    X = df.drop(columns=["Label", "Target"], errors="ignore")
    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([float("inf"), float("-inf")], float("nan"))

    y = df["Target"]

    # Sample rows while preserving the benign/attack ratio.
    if len(df) > MAX_ROWS:
        X, _, y, _ = train_test_split(
            X,
            y,
            train_size=MAX_ROWS,
            random_state=RANDOM_STATE,
            stratify=y,
        )

    if y.nunique() < 2:
        raise ValueError(
            "Only one target class was found. "
            "Check the dataset label distribution."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )


    # Check for identical feature rows in training and testing data
    train_hashes = set(
        pd.util.hash_pandas_object(
            X_train,
            index=False,
        )
    )

    test_hashes = set(
        pd.util.hash_pandas_object(
            X_test,
            index=False,
        )
    )

    overlap = train_hashes.intersection(test_hashes)

    print("\n--- DATA LEAKAGE CHECK ---")
    print("Unique training rows:", len(train_hashes))
    print("Unique testing rows:", len(test_hashes))
    print("Matching rows across splits:", len(overlap))

    
    models = {
        "decision_tree": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("classifier", DecisionTreeClassifier(
                max_depth=15,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            )),
        ]),
        "random_forest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("classifier", RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )),
        ]),
    }


    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    summary = {}

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)

        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)

        print(f"\n{name} accuracy: {accuracy:.4f}")
        print(
            classification_report(
                y_test,
                predictions,
                labels=[0, 1],
                target_names=["BENIGN", "ATTACK"],
                zero_division=0,
            )
        )
        print("Confusion matrix (rows=actual, columns=predicted):")
        print(confusion_matrix(y_test, predictions, labels=[0, 1]))

        joblib.dump(
            {
                "model": model,
                "feature_columns": list(X.columns),
                "classes": ["BENIGN", "ATTACK"],
            },
            MODEL_DIR / f"{name}.joblib",
        )

        summary[name] = {
            "accuracy": float(accuracy),
            "classification_report": classification_report(
                y_test,
                predictions,
                labels=[0, 1],
                target_names=["BENIGN", "ATTACK"],
                output_dict=True,
                zero_division=0,
            ),
            "confusion_matrix": confusion_matrix(
                y_test, predictions, labels=[0, 1]
            ).tolist(),
        }

    with open(REPORT_DIR / "model_results.json", "w") as file:
        json.dump(summary, file, indent=2)

    print("\nTraining completed.")
    print("Saved models in:", MODEL_DIR.resolve())
    print("Saved evaluation report in:", REPORT_DIR.resolve())


if __name__ == "__main__":
    main()
