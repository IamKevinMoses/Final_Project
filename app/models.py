from datetime import datetime
from flask_login import UserMixin
from app.database import db


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    first_name = db.Column(
        db.String(50),
        nullable=False
    )

    last_name = db.Column(
        db.String(50),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default="User"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    predictions = db.relationship(
        "PredictionHistory",
        backref="user",
        lazy=True
    )


class PredictionHistory(db.Model):

    __tablename__ = "prediction_history"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Location
    country = db.Column(
        db.String(50),
        nullable=False
    )

    region = db.Column(
        db.String(50),
        nullable=False
    )

    # Prediction result
    prediction = db.Column(
        db.String(20),
        nullable=False
    )

    confidence = db.Column(
        db.Float,
        nullable=False
    )

    priority = db.Column(
        db.String(100),
        nullable=False
    )

    prediction_date = db.Column(
        db.DateTime,
        default=datetime.now,
        nullable=False
    )

    # Water source details
    water_source = db.Column(
        db.String(100),
        nullable=True
    )

    treatment_method = db.Column(
        db.String(100),
        nullable=True
    )

    # Water quality details
    contaminant_level = db.Column(
        db.Float,
        nullable=True
    )

    ph = db.Column(
        db.Float,
        nullable=True
    )

    turbidity = db.Column(
        db.Float,
        nullable=True
    )

    dissolved_oxygen = db.Column(
        db.Float,
        nullable=True
    )

    nitrate_level = db.Column(
        db.Float,
        nullable=True
    )

    lead_concentration = db.Column(
        db.Float,
        nullable=True
    )

    bacteria_count = db.Column(
        db.Float,
        nullable=True
    )

    # Environmental details
    rainfall = db.Column(
        db.Float,
        nullable=True
    )

    temperature = db.Column(
        db.Float,
        nullable=True
    )

    population_density = db.Column(
        db.Float,
        nullable=True
    )

    # Socioeconomic details
    clean_water_access = db.Column(
        db.Float,
        nullable=True
    )

    healthcare_access = db.Column(
        db.Float,
        nullable=True
    )

    sanitation_coverage = db.Column(
        db.Float,
        nullable=True
    )

    urbanization = db.Column(
        db.Float,
        nullable=True
    )

    gdp_per_capita = db.Column(
        db.Float,
        nullable=True
    )

    infant_mortality_rate = db.Column(
        db.Float,
        nullable=True
    )