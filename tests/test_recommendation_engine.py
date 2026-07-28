import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from app.recommendation_engine import generate_recommendations


sample_input = {
    "bacteria_count": 420,
    "contaminant_level": 4.2,
    "turbidity": 6.5,
    "sanitation_coverage": 48,
    "clean_water_access": 55,
    "healthcare_access": 52,
    "lead": 6.2,
    "rainfall": 2700
}


result = generate_recommendations(
    prediction="High",
    input_data=sample_input
)

print("Priority:")
print(result["priority"])

print("\nKey Factors:")
for factor in result["key_factors"]:
    print("-", factor)

print("\nRecommendations:")
for item in result["recommendations"]:
    print("-", item)