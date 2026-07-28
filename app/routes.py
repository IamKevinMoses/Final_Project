from datetime import datetime
import csv
from io import StringIO

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import func

from app import bcrypt
from app.database import db
from app.models import PredictionHistory, User
from app.predictor import predict_risk
from app.recommendation_engine import generate_recommendations
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


main_bp = Blueprint("main", __name__)

def generate_password_reset_token(user):
    """
    Generate a signed password-reset token.

    The current password hash is included so that the token becomes
    invalid immediately after the password is changed.
    """
    serializer = URLSafeTimedSerializer(
    current_app.config["SECRET_KEY"]
)

    return serializer.dumps(
        {
            "user_id": user.id,
            "password_hash": user.password,
        },
        salt="password-reset",
    )


def verify_password_reset_token(token, max_age=1800):
    """
    Verify a reset token.

    max_age=1800 means the link expires after 30 minutes.
    """
    serializer = URLSafeTimedSerializer(
    current_app.config["SECRET_KEY"]
)

    try:
        token_data = serializer.loads(
            token,
            salt="password-reset",
            max_age=max_age,
        )

    except SignatureExpired:
        return None, "expired"

    except BadSignature:
        return None, "invalid"

    user = db.session.get(
        User,
        token_data.get("user_id"),
    )

    if user is None:
        return None, "invalid"

    if user.password != token_data.get("password_hash"):
        return None, "used"

    return user, None

def validate_prediction_inputs(input_data):
    """
    Validate prediction input values.

    Returns a list of user-friendly error messages.
    """

    errors = []

    if not input_data["country"]:
        errors.append("Country is required.")

    if not input_data["region"]:
        errors.append("Region is required.")

    if not 0 <= input_data["ph"] <= 14:
        errors.append("pH must be between 0 and 14.")

    if input_data["contaminant_level"] < 0:
        errors.append(
            "Contaminant level cannot be negative."
        )

    if input_data["turbidity"] < 0:
        errors.append(
            "Turbidity cannot be negative."
        )

    if input_data["dissolved_oxygen"] < 0:
        errors.append(
            "Dissolved oxygen cannot be negative."
        )

    if input_data["nitrate"] < 0:
        errors.append(
            "Nitrate level cannot be negative."
        )

    if input_data["lead"] < 0:
        errors.append(
            "Lead concentration cannot be negative."
        )

    if input_data["bacteria_count"] < 0:
        errors.append(
            "Bacteria count cannot be negative."
        )

    if input_data["rainfall"] < 0:
        errors.append(
            "Rainfall cannot be negative."
        )

    if not -50 <= input_data["temperature"] <= 60:
        errors.append(
            "Temperature must be between -50°C and 60°C."
        )

    if input_data["population_density"] < 0:
        errors.append(
            "Population density cannot be negative."
        )

    percentage_fields = {
        "Clean water access": (
            input_data["clean_water_access"]
        ),
        "Healthcare access": (
            input_data["healthcare_access"]
        ),
        "Sanitation coverage": (
            input_data["sanitation_coverage"]
        ),
        "Urbanization": (
            input_data["urbanization"]
        ),
    }

    for field_name, value in percentage_fields.items():

        if not 0 <= value <= 100:
            errors.append(
                f"{field_name} must be between 0 and 100%."
            )

    if input_data["gdp_per_capita"] < 0:
        errors.append(
            "GDP per capita cannot be negative."
        )

    if input_data["infant_mortality_rate"] < 0:
        errors.append(
            "Infant mortality rate cannot be negative."
        )

    return errors

@main_bp.route("/")
def home():
    """Display the public home page."""
    return render_template("index.html")


@main_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("main.register"))

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            flash("Email already registered.", "danger")
            return redirect(url_for("main.register"))

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        if User.query.count() == 0:
            role = "Admin"
        else:
            role = "User"

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
            role=role,
        )

        db.session.add(new_user)
        db.session.commit()

        flash(
            "Registration successful! Please login.",
            "success",
        )

        return redirect(url_for("main.login"))

    return render_template("register.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:

        if current_user.role == "Admin":
            return redirect(
                url_for("main.admin_dashboard")
            )

        return redirect(url_for("main.dashboard"))

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and bcrypt.check_password_hash(
            user.password,
            password,
        ):
            login_user(user)

            flash(
                f"Welcome, {user.first_name}!",
                "success",
            )

            if user.role == "Admin":
                return redirect(
                    url_for("main.admin_dashboard")
                )

            return redirect(url_for("main.dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("main.login"))

    return render_template("login.html")

@main_bp.route(
    "/forgot-password",
    methods=["GET", "POST"],
)
def forgot_password():

    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            "",
        ).strip().lower()

        user = User.query.filter_by(
            email=email
        ).first()

        reset_url = None

        if user:
            token = generate_password_reset_token(user)

            reset_url = url_for(
                "main.reset_password",
                token=token,
                _external=True,
            )

        return render_template(
            "reset_link.html",
            reset_url=reset_url,
        )

    return render_template(
        "forgot_password.html"
    )

@main_bp.route(
    "/reset-password/<token>",
    methods=["GET", "POST"],
)
def reset_password(token):

    if current_user.is_authenticated:
        logout_user()

    user, token_error = verify_password_reset_token(
        token
    )

    if token_error == "expired":

        flash(
            "This password reset link has expired. "
            "Please request a new link.",
            "danger",
        )

        return redirect(
            url_for("main.forgot_password")
        )

    if token_error == "used":

        flash(
            "This password reset link has already been used.",
            "danger",
        )

        return redirect(
            url_for("main.forgot_password")
        )

    if token_error == "invalid" or user is None:

        flash(
            "This password reset link is invalid.",
            "danger",
        )

        return redirect(
            url_for("main.forgot_password")
        )

    if request.method == "POST":

        password = request.form.get(
            "password",
            "",
        )

        confirm_password = request.form.get(
            "confirm_password",
            "",
        )

        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "danger",
            )

            return redirect(
                url_for(
                    "main.reset_password",
                    token=token,
                )
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger",
            )

            return redirect(
                url_for(
                    "main.reset_password",
                    token=token,
                )
            )

        user.password = (
            bcrypt.generate_password_hash(
                password
            ).decode("utf-8")
        )

        db.session.commit()

        flash(
            "Your password has been reset successfully. "
            "You can now log in.",
            "success",
        )

        return redirect(
            url_for("main.login")
        )

    return render_template(
        "reset_password.html",
        token=token,
    )

@main_bp.route("/dashboard")
@login_required
def dashboard():

    if current_user.role == "Admin":
        return redirect(
            url_for("main.admin_dashboard")
        )

    return render_template("dashboard.html")


@main_bp.route("/admin-dashboard")
@login_required
def admin_dashboard():

    if current_user.role != "Admin":

        flash(
            "You are not authorized to access that page.",
            "danger",
        )

        return redirect(url_for("main.dashboard"))

    total_users = User.query.count()

    total_predictions = (
        PredictionHistory.query.count()
    )

    high_count = (
        PredictionHistory.query
        .filter_by(prediction="High")
        .count()
    )

    medium_count = (
        PredictionHistory.query
        .filter_by(prediction="Medium")
        .count()
    )

    low_count = (
        PredictionHistory.query
        .filter_by(prediction="Low")
        .count()
    )

    recent_predictions = (
        PredictionHistory.query
        .order_by(
            PredictionHistory.prediction_date.desc()
        )
        .limit(10)
        .all()
    )

    country_stats = (
        db.session.query(
            PredictionHistory.country,
            func.count(PredictionHistory.id),
        )
        .group_by(PredictionHistory.country)
        .order_by(
            func.count(
                PredictionHistory.id
            ).desc()
        )
        .all()
    )

    dashboard_data = {
        "risk_labels": [
            "High Risk",
            "Medium Risk",
            "Low Risk",
        ],
        "risk_counts": [
            high_count,
            medium_count,
            low_count,
        ],
        "country_labels": [
            country
            for country, count in country_stats
        ],
        "country_counts": [
            count
            for country, count in country_stats
        ],
    }

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_predictions=total_predictions,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        recent_predictions=recent_predictions,
        dashboard_data=dashboard_data,
    )


@main_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have logged out successfully.",
        "success",
    )

    return redirect(url_for("main.login"))


@main_bp.route(
    "/prediction",
    methods=["GET", "POST"],
)
@login_required
def prediction():

    result = None
    error = None

    if request.method == "POST":

        try:
            input_data = {
                "year": datetime.now().year,

                "country": (
                    request.form["country"].strip()
                ),

                "region": (
                    request.form["region"].strip()
                ),

                "water_source_type": (
                    request.form[
                        "water_source_type"
                    ]
                ),

                "water_treatment_method": (
                    request.form[
                        "water_treatment_method"
                    ]
                ),

                "contaminant_level": float(
                    request.form[
                        "contaminant_level"
                    ]
                ),

                "ph": float(
                    request.form["ph"]
                ),

                "turbidity": float(
                    request.form["turbidity"]
                ),

                "dissolved_oxygen": float(
                    request.form[
                        "dissolved_oxygen"
                    ]
                ),

                "nitrate": float(
                    request.form["nitrate"]
                ),

                "lead": float(
                    request.form["lead"]
                ),

                "bacteria_count": float(
                    request.form[
                        "bacteria_count"
                    ]
                ),

                "clean_water_access": float(
                    request.form[
                        "clean_water_access"
                    ]
                ),

                "infant_mortality_rate": float(
                    request.form[
                        "infant_mortality_rate"
                    ]
                ),

                "gdp_per_capita": float(
                    request.form[
                        "gdp_per_capita"
                    ]
                ),

                "healthcare_access": float(
                    request.form[
                        "healthcare_access"
                    ]
                ),

                "urbanization": float(
                    request.form[
                        "urbanization"
                    ]
                ),

                "sanitation_coverage": float(
                    request.form[
                        "sanitation_coverage"
                    ]
                ),

                "rainfall": float(
                    request.form["rainfall"]
                ),

                "temperature": float(
                    request.form["temperature"]
                ),

                "population_density": float(
                    request.form[
                        "population_density"
                    ]
                ),
            }

            validation_errors = validate_prediction_inputs(input_data)

            if validation_errors:

                return render_template(
        "prediction.html",
        result=None,
        error=None,
        validation_errors=validation_errors,
        form_data=request.form,

                )

            result = predict_risk(input_data)

            recommendation_result = (
                generate_recommendations(
                    result["prediction"],
                    input_data,
                )
            )

            result["priority"] = (
                recommendation_result[
                    "priority"
                ]
            )

            result["key_factors"] = (
                recommendation_result[
                    "key_factors"
                ]
            )

            result["recommendations"] = (
                recommendation_result[
                    "recommendations"
                ]
            )

            new_prediction = PredictionHistory(
                user_id=current_user.id,

                # Location
                country=input_data["country"],
                region=input_data["region"],

                # Prediction result
                prediction=result["prediction"],
                confidence=result["confidence"],
                priority=result["priority"],

                # Water source
                water_source=(
                    input_data[
                        "water_source_type"
                    ]
                ),

                treatment_method=(
                    input_data[
                        "water_treatment_method"
                    ]
                ),

                # Water quality
                contaminant_level=(
                    input_data[
                        "contaminant_level"
                    ]
                ),

                ph=input_data["ph"],

                turbidity=(
                    input_data["turbidity"]
                ),

                dissolved_oxygen=(
                    input_data[
                        "dissolved_oxygen"
                    ]
                ),

                nitrate_level=(
                    input_data["nitrate"]
                ),

                lead_concentration=(
                    input_data["lead"]
                ),

                bacteria_count=(
                    input_data[
                        "bacteria_count"
                    ]
                ),

                # Environmental
                rainfall=input_data["rainfall"],

                temperature=(
                    input_data["temperature"]
                ),

                population_density=(
                    input_data[
                        "population_density"
                    ]
                ),

                # Socioeconomic
                clean_water_access=(
                    input_data[
                        "clean_water_access"
                    ]
                ),

                healthcare_access=(
                    input_data[
                        "healthcare_access"
                    ]
                ),

                sanitation_coverage=(
                    input_data[
                        "sanitation_coverage"
                    ]
                ),

                urbanization=(
                    input_data["urbanization"]
                ),

                gdp_per_capita=(
                    input_data[
                        "gdp_per_capita"
                    ]
                ),

                infant_mortality_rate=(
                    input_data[
                        "infant_mortality_rate"
                    ]
                ),
            )

            db.session.add(new_prediction)
            db.session.commit()

        except (ValueError, KeyError) as exc:

            db.session.rollback()

            print(
                "INPUT ERROR:",
                repr(exc),
            )

            error = (
                "Please complete every required field using valid "
                "numeric values."
            )

        except Exception as exc:

            db.session.rollback()

            print(
                "PREDICTION ERROR:",
                repr(exc),
            )

            error = (
                "The prediction could not be completed. "
                "Please check the entered values."
            )

    return render_template(
        "prediction.html",
        result=result,
        error=error,
        validation_errors=None,
        form_data=request.form,
    )


@main_bp.route("/prediction-history")
@login_required
def prediction_history():

    country = request.args.get(
        "country",
        "",
    ).strip()

    risk_level = request.args.get(
        "risk_level",
        "",
    ).strip()

    query = PredictionHistory.query.filter_by(
        user_id=current_user.id
    )

    if country:
        query = query.filter(
            PredictionHistory.country == country
        )

    if risk_level:
        query = query.filter(
            PredictionHistory.prediction
            == risk_level
        )

    predictions = (
        query
        .order_by(
            PredictionHistory.prediction_date.desc()
        )
        .all()
    )

    countries = (
        db.session.query(
            PredictionHistory.country
        )
        .filter_by(
            user_id=current_user.id
        )
        .distinct()
        .order_by(
            PredictionHistory.country
        )
        .all()
    )

    country_list = [
        item[0]
        for item in countries
    ]

    return render_template(
        "prediction_history.html",
        predictions=predictions,
        countries=country_list,
        selected_country=country,
        selected_risk=risk_level,
    )


@main_bp.route(
    "/prediction-history/export"
)
@login_required
def export_prediction_history():

    country = request.args.get(
        "country",
        "",
    ).strip()

    risk_level = request.args.get(
        "risk_level",
        "",
    ).strip()

    query = PredictionHistory.query.filter_by(
        user_id=current_user.id
    )

    if country:
        query = query.filter(
            PredictionHistory.country == country
        )

    if risk_level:
        query = query.filter(
            PredictionHistory.prediction
            == risk_level
        )

    predictions = (
        query
        .order_by(
            PredictionHistory.prediction_date.desc()
        )
        .all()
    )

    output = StringIO(newline="")

    writer = csv.writer(output)

    writer.writerow(
        [
            "Date",
            "Country",
            "Region",
            "Risk Level",
            "Confidence (%)",
            "Priority",
        ]
    )

    for prediction_record in predictions:

        writer.writerow(
            [
                prediction_record
                .prediction_date
                .strftime("%Y-%m-%d %H:%M"),

                prediction_record.country,

                prediction_record.region,

                prediction_record.prediction,

                f"{prediction_record.confidence:.2f}",

                prediction_record.priority,
            ]
        )

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                "attachment; "
                "filename=prediction_history.csv"
            )
        },
    )

@main_bp.route("/prediction/<int:prediction_id>")
@login_required
def prediction_details(prediction_id):

    prediction = PredictionHistory.query.filter_by(
        id=prediction_id,
        user_id=current_user.id
    ).first_or_404()

    input_data = {
        "water_source_type": prediction.water_source,
        "water_treatment_method": prediction.treatment_method,
        "contaminant_level": prediction.contaminant_level,
        "ph": prediction.ph,
        "turbidity": prediction.turbidity,
        "dissolved_oxygen": prediction.dissolved_oxygen,
        "nitrate": prediction.nitrate_level,
        "lead": prediction.lead_concentration,
        "bacteria_count": prediction.bacteria_count,
        "rainfall": prediction.rainfall,
        "temperature": prediction.temperature,
        "population_density": prediction.population_density,
        "clean_water_access": prediction.clean_water_access,
        "healthcare_access": prediction.healthcare_access,
        "sanitation_coverage": prediction.sanitation_coverage,
        "urbanization": prediction.urbanization,
        "gdp_per_capita": prediction.gdp_per_capita,
        "infant_mortality_rate": prediction.infant_mortality_rate,
    }

    recommendation_result = generate_recommendations(
        prediction.prediction,
        input_data
    )

    return render_template(
        "prediction_details.html",
        prediction=prediction,
        recommendations=recommendation_result
    )