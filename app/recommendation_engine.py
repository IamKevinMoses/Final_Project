def generate_recommendations(prediction, input_data):
    recommendations = []
    key_factors = []

    #Base recommendations by predicted risk
    if prediction == "Low":
        priority = "Routine Monitoring"

        recommendations.extend([
            "Continue regular water-quality monitoring.",
            "Maintain the existing water-treatment process.",
            "Promote routine hygiene and sanitation awareness.",
            "Inspect water-storage facilities regularly."
        ])

    elif prediction == "Medium":
        priority = "Preventive Action Recommended"

        recommendations.extend([
            "Increase the frequency of water-quality monitoring.",
            "Review chlorination and filtration procedures.",
            "Inspect sanitation and drainage facilities.",
            "Strengthen community hygiene awareness.",
            "Monitor local disease symptoms and reports."
        ])

    elif prediction == "High":
        priority = "Immediate Intervention Required"

        recommendations.extend([
            "Conduct immediate laboratory testing of the water source.",
            "Provide safe alternative drinking-water supplies.",
            "Apply appropriate water treatment before consumption.",
            "Increase public-health surveillance in the affected area.",
            "Notify the relevant local health or water authority.",
            "Launch an urgent community awareness campaign."
        ])

    else:
        priority = "Unable to Determine Priority"

    #Targeted recommendations based on inputs
    if input_data["bacteria_count"] > 300:
        key_factors.append("High bacteria count")
        recommendations.append(
            "Carry out immediate microbial testing and disinfection."
        )

    if input_data["contaminant_level"] > 3:
        key_factors.append("High contaminant level")
        recommendations.append(
            "Investigate pollution sources and strengthen water treatment."
        )

    if input_data["turbidity"] > 5:
        key_factors.append("High turbidity")
        recommendations.append(
            "Improve filtration before applying disinfection."
        )

    if input_data["sanitation_coverage"] < 60:
        key_factors.append("Low sanitation coverage")
        recommendations.append(
            "Improve access to safe sanitation facilities."
        )

    if input_data["clean_water_access"] < 70:
        key_factors.append("Limited clean-water access")
        recommendations.append(
            "Expand access to treated and safely managed drinking water."
        )

    if input_data["healthcare_access"] < 60:
        key_factors.append("Limited healthcare access")
        recommendations.append(
            "Increase medical outreach and local disease surveillance."
        )

    if input_data["lead"] > 5:
        key_factors.append("Elevated lead concentration")
        recommendations.append(
            "Inspect pipes and water infrastructure for heavy-metal contamination."
        )

    if input_data["rainfall"] > 2500:
        key_factors.append("Heavy annual rainfall")
        recommendations.append(
            "Prepare for contamination risks associated with flooding and runoff."
        )

    #Remove duplicate recommendations
    recommendations = list(dict.fromkeys(recommendations))

    return {
        "priority": priority,
        "key_factors": key_factors,
        "recommendations": recommendations
    }