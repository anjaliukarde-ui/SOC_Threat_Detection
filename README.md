# AI/ML-Based SOC Threat Detection Dashboard and Real-Time Alert System

A Python and Streamlit application that analyzes uploaded network-flow
CSV files, predicts whether each record is **BENIGN** or **ATTACK**,
displays summary results, and exports a detection report. SQLite can be
used to store analysis history.

> **Scope note:** The current version is CSV-based. It does not directly
> capture live network packets, block traffic, or automatically respond
> to attacks. Model predictions are indicators for review, not proof of
> malicious activity.

## Contents

-   [Overview](#overview)
-   [Objectives and features](#objectives-and-features)
-   [Technology stack](#technology-stack)
-   [Workflow](#workflow)
-   [Dataset and labels](#dataset-and-labels)
-   [Models and parameters](#models-and-parameters)
-   [Probability threshold](#probability-threshold)
-   [Project structure](#project-structure)
-   [Setup and execution](#setup-and-execution)
-   [Dashboard usage](#dashboard-usage)
-   [Evaluation and validation](#evaluation-and-validation)
-   [Reports and database](#reports-and-database)
-   [Troubleshooting](#troubleshooting)
-   [Limitations and future work](#limitations-and-future-work)
-   [Responsible use](#responsible-use)

## Overview

Security Operations Centers (SOCs) inspect network activity to identify
suspicious behavior. This project uses supervised machine learning to
classify network-flow records and presents the results in a simple
dashboard.

The current model performs **binary classification**: - `0` = BENIGN -
`1` = ATTACK (any original label other than BENIGN)

It does not identify the exact attack family (for example, DDoS versus
PortScan) unless a separate multiclass model is added.

## Objectives and features

-   Train and compare Decision Tree and Random Forest classifiers.
-   Upload compatible network-flow CSV files for analysis.
-   Select a trained model in the dashboard.
-   Adjust the attack-score threshold.
-   View prediction summaries, risk/severity indicators, and charts
    available in the current app.
-   Download a CSV detection report.
-   Store and review analysis history using SQLite, if enabled.
-   Save model evaluation results in JSON format.

## Technology stack

  Technology       Purpose
  ---------------- ------------------------------------------------
  Python           Main programming language
  pandas / NumPy   Data handling and numerical processing
  scikit-learn     Machine learning and evaluation
  joblib           Saving and loading trained models
  Streamlit        Web dashboard
  Plotly           Interactive charts, if used in the current app
  SQLite           Local analysis history
  VS Code          Development environment
  CICIDS2017       Network-flow dataset used for development

The `requirements.txt` file is the source of truth for dependencies.

## Workflow

1.  Load CICIDS2017 or another compatible network-flow CSV dataset.
2.  Preprocess data: normalize column names, convert features to numeric
    form, handle invalid values, and remove unusable/duplicate rows
    according to the preprocessing code.
3.  Map labels to BENIGN (`0`) and ATTACK (`1`).
4.  Split data into training and testing partitions.
5.  Train Decision Tree and Random Forest models.
6.  Evaluate using accuracy, precision, recall, F1-score, and a
    confusion matrix.
7.  Save model files under `models/` and evaluation output under
    `reports/`.
8.  Launch the Streamlit dashboard.
9.  Upload a compatible CSV, choose a model and threshold, inspect
    results, and download the report.
10. Store analysis history in SQLite if the history feature is enabled.

## Dataset and labels

The project uses CICIDS2017 network-flow CSV data, which includes benign
traffic and multiple attack categories such as DoS, DDoS, PortScan, Bot,
credential attacks, and web attacks.

Exact row counts, columns, and file sizes depend on the specific files
and release you have. Check your local CSVs for exact counts. CICIDS2017
flow files commonly contain numeric traffic features and a label column,
but column layouts can vary by file/version.

**Important:** If the model is trained as binary BENIGN/ATTACK, it
predicts only those two categories. If an original `Label` column is
included in an uploaded CSV, ensure the application does not
accidentally use it as a prediction feature.

## Models and parameters

### Decision Tree

A Decision Tree learns feature-based rules. It is relatively easy to
explain and useful as a baseline, but a deep tree may overfit.

### Random Forest

A Random Forest combines predictions from multiple decision trees. It
often generalizes better than a single tree, at the cost of additional
computation and reduced interpretability.

The described training version has used these settings; check
`train_model.py` to confirm your current values:

  Parameter                 Decision Tree   Random Forest
  ---------------------- ---------------- ---------------
  `max_depth`                        `15`            `15`
  `class_weight`             `"balanced"`    `"balanced"`
  `random_state`                     `42`            `42`
  `n_estimators`           Not applicable           `100`
  `n_jobs`                 Not applicable            `-1`
  Maximum sampled rows           `100000`        `100000`

The described setup uses an 80/20 train/test split. Parameters interact:
deeper trees can capture complex patterns but may overfit; more forest
trees may improve stability but use more resources. Balanced class
weights adjust the importance of classes but do not replace proper
validation.

## Probability threshold

If the app uses `attack_score >= threshold`, a flow with a score of 70%
is classified as ATTACK at thresholds of 30%, 50%, or 70%, but not at
80%.

-   **Lower threshold (e.g. 30%)**: usually flags more flows; recall may
    increase, but false positives may also increase.
-   **Default threshold (e.g. 50%)**: applies the configured default
    decision boundary.
-   **Higher threshold (e.g. 80%)**: usually flags fewer flows; false
    positives may decrease, but more attacks may be missed.

Changing the threshold does not change the original data or retrain the
model. It changes the decision made from the model score, so prediction
counts and downloaded reports may change. Model scores are not
necessarily calibrated real-world probabilities.

## Project structure

Representative structure based on the project setup; keep only the files
that exist in your local project.

``` text
SOC_Threat_Detection/
├── app.py
├── train_model.py
├── check_duplicates.py
├── check_labels.py
├── requirements.txt
├── data/
│   ├── MachineLearningCSV/
│   ├── processed/
│   │   └── soc_cleaned.csv
│   └── soc_history.db
├── models/
│   ├── decision_tree.joblib
│   └── random_forest.joblib
├── reports/
│   └── model_results.json
└── src/
    ├── preprocessing.py
    ├── risk_engine.py
    ├── db.py
    └── alerts.py
```

-   `app.py`: Streamlit interface, file upload, predictions, visual
    summaries, report export, and history interface.
-   `train_model.py`: training, evaluation, and model/report saving.
-   `src/preprocessing.py`: dataset preparation, if present.
-   `src/db.py`: SQLite history functions, if present.
-   `src/risk_engine.py` / `src/alerts.py`: risk and alert helpers, if
    present.
-   `models/`: trained model files.
-   `reports/`: evaluation output.
-   `data/processed/`: processed dataset.
-   `data/soc_history.db`: local database, if configured at this path.

## Setup and execution

### Requirements

-   Python compatible with `requirements.txt` (the project was
    previously run with Python 3.13.7).
-   VS Code or a terminal.
-   Dataset CSV files.
-   Enough disk space and memory for preprocessing/training.

### 1. Open the project root

Open the `SOC_Threat_Detection` folder in VS Code. Open **Terminal → New
Terminal**. Run commands from the folder containing `app.py` and
`train_model.py`.

### 2. Create and activate a virtual environment (Windows PowerShell)

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell activation is blocked, use Command Prompt:

``` bat
venv\Scripts\activate.bat
```

### 3. Install packages

``` powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If the requirements file is incomplete, the commonly used packages are:

``` powershell
pip install pandas numpy scikit-learn joblib streamlit plotly
```

### 4. Preprocess data, if needed

``` powershell
python src/preprocessing.py
```

Use the actual entry-point filename if your code differs. Confirm that
`data/processed/soc_cleaned.csv` is created if that is the path used by
`train_model.py`.

### 5. Train and evaluate

``` powershell
python train_model.py
```

Check the console output and confirm that model files and evaluation
results were saved.

### 6. Launch the dashboard

``` powershell
python -m streamlit run app.py
```

Open the local URL printed in the terminal (often
`http://localhost:8501`). Keep the terminal open while using the
dashboard. Press `Ctrl+C` in the terminal to stop it.

If the processed CSV and model files already exist and are current, you
can launch the dashboard directly without rerunning
preprocessing/training.

## Dashboard usage

1.  Start Streamlit.
2.  Choose the available model.
3.  Set the threshold; start with 50% if that is the configured default.
4.  Upload a CSV with compatible feature columns.
5.  Wait for processing to finish.
6.  Review predicted classes, counts, scores, alerts, severity
    indicators, and charts available in the current app.
7.  Download the detection report CSV.
8.  Review past analyses if database history is enabled.

For a fair threshold comparison, use the same input file and model at
30%, 50%, and 80%. Compare alert counts and, if ground-truth labels are
available, precision, recall, and false-positive rates.

## Evaluation and validation

A previous training run reported these results on a random holdout set
of approximately 20,000 rows. They are historical results and may differ
if the data or code changes.

  Metric               Decision Tree   Random Forest
  ------------------ --------------- ---------------
  Accuracy                    99.71%          99.78%
  BENIGN test rows            16,059          16,059
  ATTACK test rows             3,941           3,941
  True negatives              16,026          16,035
  False positives                 33              24
  False negatives                 25              20
  True positives               3,916           3,921

Confusion matrices in `[[TN, FP], [FN, TP]]` order:

Decision Tree:

``` text
[[16026, 33],
 [   25, 3916]]
```

Random Forest:

``` text
[[16035, 24],
 [   20, 3921]]
```

-   **Accuracy:** fraction of all rows classified correctly.
-   **Precision:** fraction of predicted attacks that are actually
    attacks.
-   **Recall:** fraction of actual attacks detected.
-   **F1-score:** harmonic mean of precision and recall.
-   **False positive:** benign traffic incorrectly flagged as attack.
-   **False negative:** attack traffic incorrectly classified as benign.

A previous row-overlap check found zero exact matching feature rows
across the random training and test partitions. This does not prove
there is no leakage through related flows, sessions, timestamps, or
capture days. Random splits can produce overly optimistic results when
similar records appear in both sets.

### Recommended independent validation

If `Tuesday-WorkingHours.pcap_ISCX.csv` is intended as a separate test
file, exclude it from training data and train the models without it.
Then evaluate it independently. Fit learned preprocessing, such as
imputation, using training data only. Tune thresholds on validation
data, not on the final test set. A prediction report alone is not enough
to calculate accuracy unless reliable ground-truth labels are compared
with the predictions correctly.

## Reports and database

The downloaded CSV usually contains the original records plus
prediction-related fields generated by the dashboard. Exact columns
depend on `app.py`; inspect the header to confirm whether it includes
predicted class, attack/risk score, severity, or alert status.

Do not assume a label column is ground truth without checking how it was
created. Keep original labels separate from predicted labels. The SQLite
database stores analysis history only as implemented in `src/db.py` and
`app.py`.

## Troubleshooting

### `ModuleNotFoundError`

Activate the virtual environment and run
`pip install -r requirements.txt`.

### Processed dataset not found

Run the preprocessing script, check the output path, and run commands
from the project root.

### Model file missing

Run `python train_model.py` and check that the filenames saved by the
script match those loaded in `app.py`.

### CSV upload or feature mismatch

The CSV must contain the feature names and meanings expected by the
model. Do not rename unrelated columns just to force compatibility.

### Dashboard fails to start

Run `python -m streamlit run app.py`, read the terminal error, verify
dependencies, and open the URL printed by Streamlit.

### Unexpected prediction counts

Verify the uploaded file, selected model, threshold, whether the code
uses `>` or `>=`, and the report's column meanings. Changing the
threshold can change predicted counts without changing model weights.

## Limitations and future work

### Current limitations

-   CSV upload rather than direct live packet capture.
-   Binary BENIGN/ATTACK prediction rather than attack-family
    classification.
-   No automatic traffic blocking or incident remediation.
-   Predictions can include false positives and false negatives.
-   Random-split performance may not represent performance on new days
    or networks.
-   Risk scores should not be treated as calibrated probabilities unless
    calibration has been evaluated.

### Possible future enhancements

-   Independent capture-day testing and validation reports.
-   Multiclass attack-family classification.
-   Probability calibration and validation-based threshold selection.
-   Model explainability and feature importance.
-   Traffic drift monitoring.
-   Authentication and role-based access.
-   Secure data-retention controls.
-   Authorized streaming-flow integration and notification services.
-   Automated tests, stronger input validation, and deployment
    packaging.

## Responsible use

Analyze only network data you are authorized to access. Reports can
contain sensitive network metadata, so store and share them carefully.
Review predictions before taking action; do not rely on a model output
alone to block traffic or attribute malicious activity.

## Academic details

-   **Project title:** AI/ML-Based SOC Threat Detection Dashboard and
    Real-Time Alert System
-   **Category:** Cybersecurity / Machine Learning
-   **Language:** Python
-   **Dashboard:** Streamlit
-   **Dataset:** CICIDS2017 network-flow CSV data


## Quick start

``` powershell
# Run from the project root with the virtual environment activated
pip install -r requirements.txt
python src/preprocessing.py
python train_model.py
python -m streamlit run app.py
```

Run preprocessing only when the processed dataset needs to be generated
or updated. If models and processed data already exist and are current,
start with:

``` powershell
python -m streamlit run app.py
```