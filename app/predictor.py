# Load the final Logistic Regression model and prepare website inputs

from pathlib import Path
from typing import Any

import joblib
import pandas as pd


# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# Path to the final deployment package
MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "aquasafe_deployment_package.pkl"
)


def load_deployment_package() -> dict[str, Any]:
    """Load and validate the final Logistic Regression deployment package."""

    # Check whether the deployment package exists
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model package was not found at: {MODEL_PATH}"
        )

    # Load the saved deployment package
    deployment_package = joblib.load(
        MODEL_PATH
    )

    # Check that all required items are available
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


#Load the deployment package once when Flask starts
deployment_package = load_deployment_package()


#Extract the final deployment components
model = deployment_package["model"]
scaler = deployment_package["scaler"]
feature_names = deployment_package["feature_names"]
class_names = deployment_package["class_names"]


# Numerical features used during model training
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


def prepare_input(
    input_data: dict[str, Any]
) -> pd.DataFrame:
    """Convert website form data into the trained model feature format."""

    # Check that all required numerical inputs are provided
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

    # Check that required categorical inputs are provided
    categorical_inputs = [
        "country",
        "region",
        "water_source_type",
        "water_treatment_method"
    ]

    missing_categorical_features = [
        feature
        for feature in categorical_inputs
        if feature not in input_data
    ]

    if missing_categorical_features:
        raise ValueError(
            "Missing categorical inputs: "
            + ", ".join(missing_categorical_features)
        )

    # Start every trained feature at zero
    model_input = {
        feature: 0.0
        for feature in feature_names
    }

    # Add numerical values from the website form
    for feature in NUMERICAL_FEATURES:
        model_input[feature] = float(
            input_data[feature]
        )

    # Create encoded categorical column names
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

    # Set matching encoded categories to 1
    # Baseline categories remain represented by zeros
    for column in categorical_columns:

        if column in model_input:
            model_input[column] = 1.0

    # Convert the prepared data into a DataFrame
    # using the exact same feature order as training
    input_df = pd.DataFrame(
        [model_input],
        columns=feature_names
    )

    return input_df


def predict_risk(
    input_data: dict[str, Any]
) -> dict[str, Any]:
    """Predict disease risk using the final Logistic Regression model."""

    # Convert website inputs into the trained feature structure
    input_df = prepare_input(
        input_data
    )

    # Apply the same scaler used during model training
    scaled_input = scaler.transform(
        input_df
    )

    # Generate the predicted risk class
    prediction = model.predict(
        scaled_input
    )[0]

    # Generate class probabilities
    probabilities = model.predict_proba(
        scaled_input
    )[0]

    # Use the highest probability as prediction confidence
    confidence = round(
        float(max(probabilities)) * 100,
        2
    )

    # Match each probability with its class name
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

    # Return prediction information to the Flask route
    return {
        "prediction": str(prediction),
        "confidence": confidence,
        "probabilities": probability_dict
    }