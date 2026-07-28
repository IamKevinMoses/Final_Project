from pathlib import Path
from typing import Any

import joblib
import pandas as pd


# Find the project root safely, regardless of where Flask is started.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "final_logistic_regression_package.pkl"
)


def load_deployment_package() -> dict[str, Any]:
    """Load and validate the saved Logistic Regression package."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model package was not found at: {MODEL_PATH}"
        )

    deployment_package = joblib.load(MODEL_PATH)

    required_items = {
        "model",
        "scaler",
        "feature_names",
        "class_names"
    }

    missing_items = required_items.difference(
        deployment_package.keys()
    )

    if missing_items:
        raise KeyError(
            "The deployment package is missing: "
            + ", ".join(sorted(missing_items))
        )

    return deployment_package


# Load once when this module is imported.
deployment_package = load_deployment_package()

model = deployment_package["model"]
scaler = deployment_package["scaler"]
feature_names = deployment_package["feature_names"]
class_names = deployment_package["class_names"]


NUMERICAL_FEATURES = [
    "year",
    "contaminant_level",
    "ph",
    "turbidity",
    "dissolved_oxygen",
    "nitrate",
    "lead",
    "bacteria_count",
    "clean_water_access",
    "infant_mortality_rate",
    "gdp_per_capita",
    "healthcare_access",
    "urbanization",
    "sanitation_coverage",
    "rainfall",
    "temperature",
    "population_density"
]


def prepare_input(input_data: dict[str, Any]) -> pd.DataFrame:
    """Convert form input into the exact 38-feature model format."""

    missing_numeric_features = [
        feature
        for feature in NUMERICAL_FEATURES
        if feature not in input_data
    ]

    if missing_numeric_features:
        raise ValueError(
            "Missing numerical inputs: "
            + ", ".join(missing_numeric_features)
        )

    # Begin with every trained feature set to zero.
    model_input = {
        feature: 0.0
        for feature in feature_names
    }

    # Insert numerical values.
    for feature in NUMERICAL_FEATURES:
        model_input[feature] = float(input_data[feature])

    # Create dummy-column names for selected categories.
    categorical_columns = [
        f"country_{input_data['country']}",
        f"region_{input_data['region']}",
        (
            "water_source_type_"
            f"{input_data['water_source_type']}"
        ),
        (
            "water_treatment_method_"
            f"{input_data['water_treatment_method']}"
        )
    ]

    # Baseline categories have no dummy column.
    # They correctly remain represented by all zeros.
    for column in categorical_columns:
        if column in model_input:
            model_input[column] = 1.0

    # Preserve the exact feature order used during training.
    return pd.DataFrame(
        [model_input],
        columns=feature_names
    )

def predict_risk(input_data):
    """
    Predict the disease risk level, confidence,
    and probabilities.
    """

    input_df = prepare_input(input_data)

    scaled_values = scaler.transform(input_df)

    prediction = model.predict(scaled_values)[0]
    probabilities = model.predict_proba(scaled_values)[0]

    confidence = round(
        float(max(probabilities)) * 100,
        2
    )

    probability_dict = {
        str(class_name): round(
            float(probability) * 100,
            2
        )
        for class_name, probability in zip(
            class_names,
            probabilities
        )
    }

    return {
        "prediction": str(prediction),
        "confidence": confidence,
        "probabilities": probability_dict
    }