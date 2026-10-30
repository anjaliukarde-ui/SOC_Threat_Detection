
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from src.db import (
    initialize_database,
    save_analysis,
    get_history,
    clear_history,
)

# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AI SOC Threat Detection",
    page_icon="🛡️",
    layout="wide",
)

MODEL_DIR = Path("models")

# Create the SQLite database and table if necessary.
initialize_database()

st.title("AI/ML-Based SOC Threat Detection")
st.caption(
    "Network traffic classification and risk analysis "
    "using machine learning"
)

# --------------------------------------------------
# 2. SIDEBAR SETTINGS
# --------------------------------------------------

st.sidebar.header("Detection Settings")

model_choice = st.sidebar.selectbox(
    "Select ML Model",
    ["Random Forest", "Decision Tree"],
)

threshold = st.sidebar.slider(
    "Attack probability threshold (%)",
    min_value=10,
    max_value=95,
    value=50,
    step=5,
)

model_file = (
    "random_forest.joblib"
    if model_choice == "Random Forest"
    else "decision_tree.joblib"
)

model_path = MODEL_DIR / model_file

# --------------------------------------------------
# 3. LOAD TRAINED MODEL
# --------------------------------------------------

if not model_path.exists():
    st.error(f"Model not found: {model_path}")
    st.info("Run python train_model.py first.")
    st.stop()

try:
    bundle = joblib.load(model_path)
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]
except Exception as exc:
    st.error(f"Could not load the trained model: {exc}")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.caption("Academic prototype — CSV-based analysis")

# --------------------------------------------------
# 4. UPLOAD NETWORK TRAFFIC CSV
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a compatible network traffic CSV",
    type=["csv"],
)

if uploaded_file is not None:
    try:
        # Read uploaded dataset.
        data = pd.read_csv(
            uploaded_file,
            low_memory=False,
        )

        data.columns = data.columns.str.strip()

        if data.empty:
            st.error("The uploaded CSV contains no records.")
            st.stop()

        # Remove labels before prediction.
        X = data.drop(
            columns=["Label", "Class", "Target"],
            errors="ignore",
        )

        # Verify required model features.
        missing = [
            col
            for col in feature_columns
            if col not in X.columns
        ]

        if missing:
            st.error(
                f"CSV is missing {len(missing)} required features."
            )
            st.write(
                "Missing feature examples:",
                missing[:10],
            )
            st.stop()

        # Convert features to numeric values.
        X = X[feature_columns].apply(
            pd.to_numeric,
            errors="coerce",
        )

        X = X.replace(
            [float("inf"), float("-inf")],
            float("nan"),
        ).fillna(0)

        # --------------------------------------------------
        # 5. PREDICT ATTACK PROBABILITY
        # --------------------------------------------------

        probabilities = model.predict_proba(X)

        classes = list(model.classes_)

        if 1 not in classes:
            st.error(
                "The selected model does not contain the "
                "expected attack class (1). Check model training."
            )
            st.stop()

        attack_index = classes.index(1)

        attack_probability = probabilities[:, attack_index]

        # Apply user-selected threshold.
        predicted_attack = (
            attack_probability * 100 >= threshold
        )

        # --------------------------------------------------
        # 6. CREATE PREDICTION RESULTS
        # --------------------------------------------------

        results = data.copy()

        results["Prediction"] = [
            "ATTACK" if flag else "BENIGN"
            for flag in predicted_attack
        ]

        results["Risk Score (%)"] = (
            attack_probability * 100
        ).round(2)

        def get_severity(is_attack, score):
            if not is_attack:
                return "Low"

            if score >= 90:
                return "Critical"
            elif score >= 75:
                return "High"
            elif score >= 50:
                return "Medium"
            else:
                return "Low"

        results["Severity"] = [
            get_severity(
                bool(flag),
                float(score) * 100,
            )
            for flag, score in zip(
                predicted_attack,
                attack_probability,
            )
        ]

        results["Alert"] = [
            "Potential attack detected"
            if flag
            else "No alert"
            for flag in predicted_attack
        ]

        # --------------------------------------------------
        # 7. CALCULATE DASHBOARD METRICS
        # --------------------------------------------------

        total = len(results)

        attacks = int(predicted_attack.sum())

        benign = total - attacks

        critical = int(
            (results["Severity"] == "Critical").sum()
        )

        high = int(
            (results["Severity"] == "High").sum()
        )

        high_critical = high + critical

        # --------------------------------------------------
        # 8. SAVE ANALYSIS TO SQLITE DATABASE
        # --------------------------------------------------

        upload_key = (
            uploaded_file.name,
            uploaded_file.size,
            model_choice,
            threshold,
        )

        if (
            st.session_state.get("last_upload_key")
            != upload_key
        ):
            save_analysis(
                file_name=uploaded_file.name,
                model_name=model_choice,
                threshold=threshold,
                total_flows=total,
                potential_attacks=attacks,
                benign_flows=benign,
                high_critical_alerts=high_critical,
            )

            st.session_state["last_upload_key"] = upload_key

        # --------------------------------------------------
        # 9. SECURITY OVERVIEW
        # --------------------------------------------------

        st.subheader("Security Overview")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Flows Analyzed",
            f"{total:,}",
        )

        c2.metric(
            "Potential Attacks",
            f"{attacks:,}",
        )

        c3.metric(
            "Benign Flows",
            f"{benign:,}",
        )

        c4.metric(
            "High/Critical Alerts",
            f"{high_critical:,}",
        )

        if critical:
            st.error(
                f"{critical} flow(s) flagged as Critical. "
                "Review and validate these records."
            )
        elif high:
            st.warning(
                f"{high} flow(s) flagged as High risk."
            )
        elif attacks:
            st.warning(
                f"{attacks} potential attack flow(s) detected."
            )
        else:
            st.success(
                "No flows crossed the selected attack threshold."
            )

        # --------------------------------------------------
        # 10. SEVERITY DISTRIBUTION
        # --------------------------------------------------

        st.subheader("Severity Distribution")

        severity_counts = (
            results["Severity"]
            .value_counts()
            .reindex(
                ["Critical", "High", "Medium", "Low"],
                fill_value=0,
            )
        )

        st.bar_chart(severity_counts)

        # --------------------------------------------------
        # 11. POTENTIAL ATTACK RECORDS
        # --------------------------------------------------

        st.subheader("Potential Attack Records")

        attack_rows = results[
            results["Prediction"] == "ATTACK"
        ]

        if attack_rows.empty:
            st.info("No records crossed the selected threshold.")
        else:
            st.dataframe(
                attack_rows,
                use_container_width=True,
            )

        # --------------------------------------------------
        # 12. ALL CLASSIFIED TRAFFIC
        # --------------------------------------------------

        st.subheader("All Classified Traffic")

        st.dataframe(
            results,
            use_container_width=True,
        )

        # --------------------------------------------------
        # 13. DOWNLOAD REPORT
        # --------------------------------------------------

        st.download_button(
            label="Download Detection Report",
            data=results.to_csv(
                index=False,
            ).encode("utf-8"),
            file_name="soc_detection_report.csv",
            mime="text/csv",
        )

        st.caption(
            "Risk score represents estimated attack probability, "
            "not confirmed real-world threat severity."
        )

        st.warning(
            "This prototype analyzes uploaded CSV records. "
            "It does not capture live network packets or "
            "automatically block attacks. Predictions require validation."
        )

    except Exception as exc:
        st.error(f"Analysis failed: {exc}")

# --------------------------------------------------
# 14. PERMANENT DETECTION HISTORY
# --------------------------------------------------

st.divider()

st.subheader("Detection History")

try:
    history = get_history()

    if history:
        history_columns = [
            "ID",
            "Analysis Time",
            "File",
            "Model",
            "Threshold (%)",
            "Flows Analyzed",
            "Potential Attacks",
            "Benign Flows",
            "High/Critical Alerts",
        ]

        history_df = pd.DataFrame(
            history,
            columns=history_columns,
        )

        st.dataframe(
            history_df,
            use_container_width=True,
        )

        if st.button("Clear Permanent History"):
            clear_history()

            st.session_state.pop(
                "last_upload_key",
                None,
            )

            st.success("Detection history cleared.")
            st.rerun()

    else:
        st.info(
            "No saved analyses yet. Upload a CSV to begin."
        )

except Exception as exc:
    st.error(
        f"Could not load detection history: {exc}"
    )
