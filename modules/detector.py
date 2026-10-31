"""
ChainSentinel AI
Machine Learning Anomaly Detection Engine

Uses:
- Scikit-learn Isolation Forest
- Explainable transaction rules
- Transparent risk classification

An anomaly is not automatically fraud.
"""

import logging
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("chainsentinel.detector")


# =========================================================
# COLUMN DETECTION
# =========================================================

COLUMN_ALIASES = {
    "amount": [
        "amount", "amount_eth", "amount (eth)",
        "value", "eth_value", "transaction_value"
    ],
    "gas": [
        "gas", "gas_price", "gas_price_gwei",
        "gas (gwei)", "gasprice"
    ]
}


def find_column(dataframe, aliases):

    lookup = {
        str(column).strip().lower(): column
        for column in dataframe.columns
    }

    for alias in aliases:
        if alias in lookup:
            return lookup[alias]

    return None


# =========================================================
# PREPARE TRANSACTION FEATURES
# =========================================================

def prepare_features(dataframe):

    if not isinstance(dataframe, pd.DataFrame):
        raise ValueError("Input must be a Pandas DataFrame.")

    if dataframe.empty:
        raise ValueError("No transaction records were provided.")

    if len(dataframe) > 100000:
        raise ValueError("Maximum 100,000 rows supported per analysis.")

    result = dataframe.copy()

    amount_column = find_column(
        result, COLUMN_ALIASES["amount"]
    )

    gas_column = find_column(
        result, COLUMN_ALIASES["gas"]
    )

    if amount_column is None:
        raise ValueError(
            "Transaction amount column not found. "
            "Use amount, amount_eth or Amount (ETH)."
        )

    result["_amount_feature"] = pd.to_numeric(
        result[amount_column], errors="coerce"
    )

    if gas_column:
        result["_gas_feature"] = pd.to_numeric(
            result[gas_column], errors="coerce"
        )
    else:
        result["_gas_feature"] = 0.0

    result["_amount_feature"] = (
        result["_amount_feature"].replace(
            [np.inf, -np.inf], np.nan
        )
    )

    result["_gas_feature"] = (
        result["_gas_feature"].replace(
            [np.inf, -np.inf], np.nan
        )
    )

    result = result.dropna(
        subset=["_amount_feature"]
    ).copy()

    if result.empty:
        raise ValueError(
            "No valid numeric transaction amounts were found."
        )

    if (result["_amount_feature"] < 0).any():
        raise ValueError(
            "Negative transaction amounts are not supported."
        )

    if (result["_gas_feature"] < 0).any():
        raise ValueError(
            "Negative gas values are not supported."
        )

    return result


# =========================================================
# EXPLAINABLE SECURITY RULES
# =========================================================

def calculate_rule_findings(dataframe):

    amounts = dataframe["_amount_feature"]
    gas_values = dataframe["_gas_feature"]

    median_amount = float(amounts.median())
    median_gas = float(gas_values.median())

    q1 = float(amounts.quantile(0.25))
    q3 = float(amounts.quantile(0.75))
    iqr = q3 - q1

    amount_threshold = q3 + (3 * iqr)

    if iqr == 0:
        amount_threshold = q3 * 3 if q3 > 0 else 0

    if median_gas > 0:
        gas_threshold = median_gas * 3
    else:
        gas_threshold = float(gas_values.quantile(0.95))

    findings = []

    for _, row in dataframe.iterrows():

        reasons = []

        amount = float(row["_amount_feature"])
        gas = float(row["_gas_feature"])

        if amount_threshold > 0 and amount > amount_threshold:
            reasons.append(
                "Transaction amount is unusually high "
                "relative to this dataset."
            )

        if gas_threshold > 0 and gas > gas_threshold:
            reasons.append(
                "Gas value is unusually high "
                "relative to this dataset."
            )

        findings.append(reasons)

    return findings


# =========================================================
# RISK CLASSIFICATION
# =========================================================

def classify_risk(is_anomaly, reasons, anomaly_score=None):

    reason_count = len(reasons)

    if reason_count >= 2 and is_anomaly:
        return "Critical"

    if is_anomaly or reason_count >= 2:
        return "High"

    if reason_count == 1:
        return "Medium"

    return "Low"


# =========================================================
# MAIN DETECTION FUNCTION
# =========================================================

def detect_anomalies(dataframe, contamination=0.10):

    """
    Analyse transaction data.

    Required:
        A numeric transaction amount column.

    Optional:
        A gas price column.

    Returns:
        A DataFrame with anomaly labels, scores,
        risk levels and explanations.
    """

    if not 0.01 <= contamination <= 0.30:
        raise ValueError(
            "Contamination must be between 0.01 and 0.30."
        )

    prepared = prepare_features(dataframe)

    prepared["rule_findings"] = calculate_rule_findings(
        prepared
    )

    prepared["is_anomaly"] = False
    prepared["anomaly_score"] = 0.0

    # Isolation Forest requires sufficient records.
    if len(prepared) >= 5:

        features = prepared[
            ["_amount_feature", "_gas_feature"]
        ].copy()

        features = features.replace(
            [np.inf, -np.inf], np.nan
        ).fillna(0)

        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)

        model = IsolationForest(
            n_estimators=150,
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )

        predictions = model.fit_predict(scaled_features)

        # Isolation Forest returns -1 for an anomaly.
        prepared["is_anomaly"] = predictions == -1

        # Higher decision scores indicate more normal records.
        prepared["anomaly_score"] = (
            -model.decision_function(scaled_features)
        )

    else:
        logger.warning(
            "Fewer than five records. Using security rules only."
        )

    prepared["risk_level"] = prepared.apply(
        lambda row: classify_risk(
            bool(row["is_anomaly"]),
            row["rule_findings"],
            float(row["anomaly_score"])
        ),
        axis=1
    )

    prepared["explanation"] = prepared.apply(
        lambda row: (
            "; ".join(row["rule_findings"])
            if row["rule_findings"]
            else (
                "Machine learning identified an unusual "
                "pattern relative to this dataset."
                if row["is_anomaly"]
                else "No anomaly identified by the configured checks."
            )
        ),
        axis=1
    )

    # Remove internal calculation columns.
    prepared.drop(
        columns=["_amount_feature", "_gas_feature"],
        inplace=True
    )

    return prepared


# =========================================================
# SUMMARY
# =========================================================

def get_detection_summary(results):

    if results.empty:
        return {
            "total": 0,
            "anomalies": 0,
            "high_risk": 0,
            "critical": 0
        }

    return {
        "total": int(len(results)),
        "anomalies": int(results["is_anomaly"].sum()),
        "high_risk": int(
            results["risk_level"].isin(
                ["High", "Critical"]
            ).sum()
        ),
        "critical": int(
            (results["risk_level"] == "Critical").sum()
        )
    }
