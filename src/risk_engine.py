
def calculate_risk(prediction, attack_probability):
    probability = float(attack_probability)
    score = round(probability * 100, 2)

    if prediction == 0:
        status = "BENIGN"
        severity = "Low"
    elif score >= 85:
        status = "ATTACK"
        severity = "Critical"
    elif score >= 65:
        status = "ATTACK"
        severity = "High"
    elif score >= 40:
        status = "ATTACK"
        severity = "Medium"
    else:
        status = "ATTACK"
        severity = "Low"

    return {
        "status": status,
        "risk_score": score,
        "severity": severity
    }
