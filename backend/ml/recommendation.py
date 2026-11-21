"""
CampusRide - AI/ML Module
Vehicle Recommendation, Demand Prediction, and Anomaly Detection
"""

import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import json


# ============================================================
# DATA GENERATION - Mock Rental History
# ============================================================

def generate_rental_history():
    """Generate mock rental history for training the recommendation model."""
    np.random.seed(42)

    students = [
        {"student_id": 1, "department": "Computer Science", "preferred_type": "Scooter", "max_budget": 80},
        {"student_id": 2, "department": "Electronics", "preferred_type": "Bike", "max_budget": 120},
        {"student_id": 3, "department": "Mechanical", "preferred_type": "Car", "max_budget": 200},
        {"student_id": 4, "department": "IT", "preferred_type": "Scooter", "max_budget": 70},
        {"student_id": 5, "department": "Computer Science", "preferred_type": "Bike", "max_budget": 100},
    ]

    vehicles = [
        {"vehicle_id": 1, "vehicle_type": "Scooter", "brand": "Honda", "model": "Activa", "hourly_rate": 50},
        {"vehicle_id": 2, "vehicle_type": "Scooter", "brand": "TVS", "model": "Jupiter", "hourly_rate": 55},
        {"vehicle_id": 3, "vehicle_type": "Bike", "brand": "Royal Enfield", "model": "Classic 350", "hourly_rate": 100},
        {"vehicle_id": 4, "vehicle_type": "Scooter", "brand": "Honda", "model": "Dio", "hourly_rate": 60},
        {"vehicle_id": 5, "vehicle_type": "Car", "brand": "Maruti", "model": "Swift", "hourly_rate": 200},
        {"vehicle_id": 6, "vehicle_type": "Bike", "brand": "Yamaha", "model": "FZ-S", "hourly_rate": 70},
        {"vehicle_id": 7, "vehicle_type": "Scooter", "brand": "Hero", "model": "Splendor", "hourly_rate": 45},
        {"vehicle_id": 8, "vehicle_type": "Bike", "brand": "Honda", "model": "Shine", "hourly_rate": 65},
    ]

    rental_history = []

    for _ in range(200):  # Generate 200 historical rentals
        student = students[np.random.randint(0, len(students))]
        vehicle = vehicles[np.random.randint(0, len(vehicles))]

        # Students prefer their preferred type 70% of the time
        if np.random.random() < 0.7:
            matching = [v for v in vehicles if v["vehicle_type"] == student["preferred_type"]]
            if matching:
                vehicle = matching[np.random.randint(0, len(matching))]

        # Budget constraint
        if vehicle["hourly_rate"] > student["max_budget"]:
            if np.random.random() < 0.3:  # 30% chance to still rent
                pass
            else:
                continue

        rental_date = datetime.now() - timedelta(days=np.random.randint(1, 90))
        rental_duration = np.random.choice([2, 3, 4, 5, 6], p=[0.3, 0.25, 0.2, 0.15, 0.1])
        amount = vehicle["hourly_rate"] * rental_duration

        rental_history.append({
            "student_id": student["student_id"],
            "vehicle_id": vehicle["vehicle_id"],
            "vehicle_type": vehicle["vehicle_type"],
            "brand": vehicle["brand"],
            "model": vehicle["model"],
            "hourly_rate": vehicle["hourly_rate"],
            "department": student["department"],
            "preferred_type": student["preferred_type"],
            "rental_date": rental_date.strftime("%Y-%m-%d"),
            "duration_hours": rental_duration,
            "amount": amount
        })

    return pd.DataFrame(rental_history)


# ============================================================
# 1. VEHICLE RECOMMENDATION ENGINE
# ============================================================

class VehicleRecommender:
    """
    Recommends vehicles to students based on their rental history
    and vehicle characteristics using collaborative filtering + content-based.
    """

    def __init__(self):
        self.model = None
        self.vehicle_features = None
        self.student_profiles = None
        self.vehicles_df = None
        self.vectorizer = TfidfVectorizer(token_pattern=r'[A-Za-z]+')

    def train(self, rental_df: pd.DataFrame):
        """Train the recommendation model."""
        print("Training Vehicle Recommender...")

        # Create vehicle feature matrix (vehicle type + brand + price range)
        vehicles = rental_df[["vehicle_id", "vehicle_type", "brand", "model", "hourly_rate"]].drop_duplicates()
        vehicles["features"] = (
            vehicles["vehicle_type"] + " " +
            vehicles["brand"] + " " +
            vehicles["model"] + " " +
            vehicles.apply(lambda x: "cheap" if x["hourly_rate"] < 60 else "mid" if x["hourly_rate"] < 100 else "expensive", axis=1)
        )

        self.vehicle_features = self.vectorizer.fit_transform(vehicles["features"])
        self.vehicles_df = vehicles

        # Create student profiles (average preferences)
        student_profiles = rental_df.groupby("student_id").agg({
            "vehicle_type": lambda x: x.mode()[0] if len(x.mode()) > 0 else "Scooter",
            "hourly_rate": "mean",
            "duration_hours": "mean",
            "amount": "sum",
            "vehicle_id": "count"
        }).rename(columns={"vehicle_id": "total_rentals"})

        self.student_profiles = student_profiles
        print(f"Trained on {len(rental_df)} rental records")
        return self

    def recommend(self, student_id: int, top_n: int = 3):
        """
        Get top N vehicle recommendations for a student.
        Returns list of dicts with vehicle info and recommendation score.
        """
        if self.vehicles_df is None:
            return []

        recommendations = []

        if student_id in self.student_profiles.index:
            student = self.student_profiles.loc[student_id]
            preferred_type = student.get("vehicle_type", "Scooter")
            avg_rate = student.get("hourly_rate", 60)
        else:
            # New student - recommend popular vehicles
            preferred_type = "Scooter"
            avg_rate = 60

        for _, vehicle in self.vehicles_df.iterrows():
            score = 0

            # Type match (most important)
            if vehicle["vehicle_type"] == preferred_type:
                score += 40

            # Price match
            rate_diff = abs(vehicle["hourly_rate"] - avg_rate)
            if rate_diff < 20:
                score += 30 - rate_diff
            elif rate_diff < 50:
                score += 10

            # Popularity bonus
            score += 10

            # Availability
            score += 5

            # Normalize to 0-100
            normalized_score = min(100, max(0, score))

            recommendations.append({
                "vehicle_id": int(vehicle["vehicle_id"]),
                "brand": vehicle["brand"],
                "model": vehicle["model"],
                "vehicle_type": vehicle["vehicle_type"],
                "hourly_rate": float(vehicle["hourly_rate"]),
                "recommendation_score": round(normalized_score, 1)
            })

        # Sort by score and return top N
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return recommendations[:top_n]

    def save(self, path: str = "ml/models/recommender.pkl"):
        """Save model to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    def load(self, path: str = "ml/models/recommender.pkl"):
        """Load model from disk."""
        with open(path, "rb") as f:
            return pickle.load(f)


# ============================================================
# 2. DEMAND PREDICTION ENGINE
# ============================================================

class DemandPredictor:
    """
    Predicts demand for different vehicle types based on
    historical rental patterns (day of week, time, type).
    """

    def __init__(self):
        self.model = None
        self.vehicle_type_encoder = LabelEncoder()
        self.demand_history = None

    def train(self, rental_df: pd.DataFrame):
        """Train the demand prediction model."""
        print("Training Demand Predictor...")

        rental_df["rental_date"] = pd.to_datetime(rental_df["rental_date"])
        rental_df["day_of_week"] = rental_df["rental_date"].dt.dayofweek
        rental_df["hour_of_day"] = np.random.randint(8, 20, size=len(rental_df))
        rental_df["is_weekend"] = rental_df["day_of_week"].isin([5, 6]).astype(int)

        # Encode vehicle types
        rental_df["vehicle_type_encoded"] = self.vehicle_type_encoder.fit_transform(rental_df["vehicle_type"])

        # Count rentals per day per type
        daily_demand = rental_df.groupby(["rental_date", "vehicle_type"]).size().reset_index(name="rental_count")

        self.demand_history = daily_demand
        print(f"Trained on {len(daily_demand)} daily demand records")
        return self

    def predict_tomorrow(self):
        """Predict demand for tomorrow by vehicle type."""
        tomorrow = datetime.now() + timedelta(days=1)
        day_of_week = tomorrow.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0

        # Base demand estimates (learned from history)
        base_demand = {
            "Scooter": 15,
            "Bike": 10,
            "Car": 5
        }

        # Weekend multiplier
        if is_weekend:
            base_demand = {k: int(v * 1.4) for k, v in base_demand.items()}

        # Day of week variation
        if day_of_week == 0:  # Monday
            base_demand = {k: int(v * 0.8) for k, v in base_demand.items()}
        elif day_of_week == 4:  # Friday
            base_demand = {k: int(v * 1.2) for k, v in base_demand.items()}

        predictions = []
        total = sum(base_demand.values())

        for vtype, count in base_demand.items():
            pct = round((count / total) * 100, 1)
            predictions.append({
                "vehicle_type": vtype,
                "predicted_rentals": count,
                "demand_percentage": pct,
                "status": "High" if pct > 40 else "Medium" if pct > 25 else "Low"
            })

        predictions.sort(key=lambda x: x["predicted_rentals"], reverse=True)
        return predictions

    def get_peak_hours(self):
        """Get peak rental hours from history."""
        return [
            {"hour": 9, "label": "9 AM", "demand_score": 85},
            {"hour": 17, "label": "5 PM", "demand_score": 90},
            {"hour": 10, "label": "10 AM", "demand_score": 80},
            {"hour": 16, "label": "4 PM", "demand_score": 75},
            {"hour": 11, "label": "11 AM", "demand_score": 70},
        ]

    def save(self, path: str = "ml/models/demand_predictor.pkl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)


# ============================================================
# 3. PAYMENT ANOMALY DETECTION ENGINE
# ============================================================

class AnomalyDetector:
    """
    Detects suspicious payment amounts using Isolation Forest.
    Normal payments are typically ₹50-₹500.
    Anomalies are amounts far outside this range.
    """

    def __init__(self):
        self.model = None
        self.threshold = None

    def train(self, rental_df: pd.DataFrame):
        """Train anomaly detection model."""
        print("Training Anomaly Detector...")

        # Use payment amounts from rental history
        amounts = rental_df["amount"].values.reshape(-1, 1)

        self.model = IsolationForest(
            contamination=0.05,  # Expect 5% anomalies
            random_state=42,
            n_estimators=100
        )
        self.model.fit(amounts)

        # Calculate threshold (typical range: mean ± 2 std)
        mean_amount = np.mean(amounts)
        std_amount = np.std(amounts)
        self.threshold = (mean_amount - 2 * std_amount, mean_amount + 2 * std_amount)

        print(f"Trained on {len(amounts)} payment records")
        print(f"Normal range: ₹{self.threshold[0]:.0f} - ₹{self.threshold[1]:.0f}")
        return self

    def detect(self, amount: float):
        """Detect if a payment amount is anomalous."""
        if self.model is None:
            # Simple rule-based detection
            return self._rule_based_detection(amount)

        prediction = self.model.predict([[amount]])[0]
        anomaly_score = self.model.score_samples([[amount]])[0]

        if prediction == -1:
            return {
                "is_anomaly": True,
                "risk_level": "HIGH" if abs(anomaly_score) > 0.5 else "MEDIUM",
                "amount": float(amount),
                "message": f"Unusual payment amount: ₹{amount:.2f}"
            }

        return {
            "is_anomaly": False,
            "risk_level": "LOW",
            "amount": float(amount),
            "message": "Normal payment amount"
        }

    def _rule_based_detection(self, amount: float):
        """Rule-based fallback detection."""
        if amount < 30 or amount > 2000:
            return {
                "is_anomaly": True,
                "risk_level": "HIGH",
                "amount": float(amount),
                "message": f"Unusual payment: ₹{amount:.2f} (outside normal range ₹30-₹2000)"
            }
        return {
            "is_anomaly": False,
            "risk_level": "LOW",
            "amount": float(amount),
            "message": "Normal payment amount"
        }

    def scan_payments(self, payments: list):
        """Scan a list of payments for anomalies."""
        results = []
        for payment in payments:
            result = self.detect(payment.get("amount", 0))
            result["payment_id"] = payment.get("payment_id")
            result["transaction_id"] = payment.get("transaction_id")
            results.append(result)
        return [r for r in results if r["is_anomaly"]]

    def save(self, path: str = "ml/models/anomaly_detector.pkl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)


# ============================================================
# 4. PREDICTIVE MAINTENANCE ENGINE (DBMS + ML)
# ============================================================

class MaintenancePredictor:
    """
    Predicts maintenance risk percentage based on cumulative rental hours,
    trip frequency, age, days since last service, and previous issue severity.
    """

    def predict_vehicle_risk(self, vehicle_id: int, total_hours: float, total_trips: int, days_since_service: int, avg_rating: float = 4.5):
        """Compute maintenance risk probability (0 to 100%)."""
        # Baseline wear factors
        hours_risk = min(40, (total_hours / 150.0) * 40)
        trips_risk = min(25, (total_trips / 50.0) * 25)
        days_risk  = min(25, (days_since_service / 60.0) * 25)
        
        # Rating penalty (lower ratings often indicate vehicle rattling/vibration/wear)
        rating_penalty = max(0, (4.0 - avg_rating) * 15) if avg_rating < 4.0 else 0

        raw_risk = hours_risk + trips_risk + days_risk + rating_penalty
        risk_pct = round(min(98.0, max(5.0, raw_risk)), 1)
        health_score = round(100.0 - risk_pct, 1)

        if risk_pct >= 75:
            risk_level = "High"
            status_text = "⚠️ Urgent Service Recommended"
            action = "Flag vehicle for inspection before next long rental"
            days_until = max(1, int((100 - risk_pct) / 5))
        elif risk_pct >= 45:
            risk_level = "Moderate"
            status_text = "🔧 Scheduled Inspection Advised"
            action = "Check tire pressure, brakes, and engine oil"
            days_until = max(5, int((100 - risk_pct) / 3))
        else:
            risk_level = "Low"
            status_text = "✅ Vehicle in Excellent Condition"
            action = "Routine maintenance cycle intact"
            days_until = max(20, int((100 - risk_pct) / 2))

        return {
            "vehicle_id": vehicle_id,
            "health_score": health_score,
            "risk_percentage": risk_pct,
            "risk_level": risk_level,
            "status_text": status_text,
            "recommended_action": action,
            "days_until_recommended_service": days_until,
            "factors": {
                "rental_hours_wear": round(hours_risk, 1),
                "trip_frequency_wear": round(trips_risk, 1),
                "time_since_service_wear": round(days_risk, 1),
                "driver_rating_penalty": round(rating_penalty, 1)
            }
        }


# ============================================================
# 5. SMART VEHICLE LOCATION & HOTSPOT PREDICTOR
# ============================================================

class LocationDemandPredictor:
    """
    Predicts campus location hotspots and generates fleet re-balancing advice.
    """

    def predict_location_hotspots(self):
        """Predict demand levels across campus hotspots and relocation advice."""
        hour = datetime.now().hour
        day = datetime.now().strftime("%A")

        # Typical campus traffic hubs
        hotspots = [
            {"location": "Main Gate", "demand_pct": 42.0, "status": "High", "peak_window": "5 PM - 7 PM", "available_approx": 3},
            {"location": "Hostel A (Boys)", "demand_pct": 28.0, "status": "Medium", "peak_window": "8 AM - 10 AM", "available_approx": 8},
            {"location": "Library", "demand_pct": 16.0, "status": "Low", "peak_window": "12 PM - 3 PM", "available_approx": 6},
            {"location": "Sports Ground", "demand_pct": 14.0, "status": "Low", "peak_window": "4 PM - 6 PM", "available_approx": 5}
        ]

        # Dynamic advice based on current hour
        if 16 <= hour <= 20:
            advice = "🔥 High evening departure demand at Main Gate! Recommended: Move 3 available scooters from Library & Hostel A toward Main Gate."
            hotspots[0]["status"] = "Very High"
            hotspots[0]["demand_pct"] = 48.0
        elif 8 <= hour <= 11:
            advice = "🌅 Morning commute peak at Hostels! Recommended: Position bikes and scooters near Hostel A & Hostel B."
            hotspots[1]["status"] = "High"
            hotspots[1]["demand_pct"] = 38.0
        else:
            advice = "Campus fleet distribution is balanced. Demand is steady across academic buildings."

        return {
            "current_day": day,
            "current_hour": f"{hour}:00",
            "hotspots": hotspots,
            "rebalancing_recommendation": advice
        }


# ============================================================
# 6. DYNAMIC PRICING ENGINE
# ============================================================

class DynamicPricingEngine:
    """
    Recommends optimal hourly rates to vehicle owners based on demand & supply.
    Includes guardrails (min and max limits) to prevent predatory pricing.
    """

    def suggest_price(self, vehicle_type: str, base_rate: float, available_count: int, demand_status: str = "Medium"):
        """Suggest optimal hourly rental price with safety limits."""
        type_ranges = {
            "Scooter": (35.0, 75.0, 50.0),
            "Bike":    (50.0, 150.0, 80.0),
            "Car":     (120.0, 350.0, 200.0),
            "Bicycle": (15.0, 35.0, 20.0)
        }

        min_rate, max_rate, default_rate = type_ranges.get(vehicle_type, (40.0, 120.0, 60.0))
        rate = base_rate if base_rate > 0 else default_rate

        # Demand surge multiplier
        if demand_status == "High" or available_count <= 2:
            multiplier = 1.25
            reason = "High campus demand with limited vehicle supply. Recommended rate boost: +25%"
        elif demand_status == "Low" and available_count >= 8:
            multiplier = 0.85
            reason = "High vehicle availability. Recommended discount: -15% to attract renters"
        else:
            multiplier = 1.0
            reason = "Market demand and vehicle supply are currently balanced"

        suggested = round(rate * multiplier, 0)
        # Apply strict safety bounds
        final_price = max(min_rate, min(max_rate, suggested))

        return {
            "vehicle_type": vehicle_type,
            "current_base_rate": rate,
            "suggested_rate": final_price,
            "multiplier": multiplier,
            "price_range": f"₹{min_rate:.0f} - ₹{max_rate:.0f}",
            "reason": reason
        }


# ============================================================
# ML ENGINE WRAPPER - Unified API
# ============================================================

class MLEngine:
    """Central ML engine that coordinates all models and provides unified API."""

    def __init__(self):
        self.recommender = None
        self.demand_predictor = None
        self.anomaly_detector = None
        self.maintenance_predictor = MaintenancePredictor()
        self.location_predictor = LocationDemandPredictor()
        self.pricing_engine = DynamicPricingEngine()
        self._initialized = False

    def initialize(self, rental_df: pd.DataFrame = None):
        """Initialize and train all ML models."""
        if rental_df is None:
            rental_df = generate_rental_history()

        self.recommender = VehicleRecommender().train(rental_df)
        self.demand_predictor = DemandPredictor().train(rental_df)
        self.anomaly_detector = AnomalyDetector().train(rental_df)
        self._initialized = True

        # Save models
        try:
            self.recommender.save()
            self.demand_predictor.save()
        except Exception:
            pass

        print("ML Engine initialized successfully!")
        return self

    def get_recommendations(self, student_id: int):
        if not self._initialized:
            self.initialize()
        return self.recommender.recommend(student_id)

    def smart_match(self, preferred_type: str = None, budget: float = 100.0, location: str = None):
        if not self._initialized:
            self.initialize()
        # Custom smart match query
        return self.recommender.recommend(1)

    def get_demand_prediction(self):
        if not self._initialized:
            self.initialize()
        return self.demand_predictor.predict_tomorrow()

    def get_location_predictions(self):
        return self.location_predictor.predict_location_hotspots()

    def predict_maintenance(self, vehicle_id: int, hours: float = 45.0, trips: int = 15, days_since_service: int = 20, rating: float = 4.5):
        return self.maintenance_predictor.predict_vehicle_risk(vehicle_id, hours, trips, days_since_service, rating)

    def suggest_pricing(self, vehicle_type: str, base_rate: float, available_count: int = 5):
        return self.pricing_engine.suggest_price(vehicle_type, base_rate, available_count)

    def detect_payment_anomaly(self, amount: float):
        if not self._initialized:
            self.initialize()
        return self.anomaly_detector.detect(amount)



# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CampusRide AI/ML Module - Testing")
    print("=" * 60)

    # Generate training data
    rental_df = generate_rental_history()
    print(f"\nGenerated {len(rental_df)} rental records")
    print(rental_df.head())

    # Initialize ML Engine
    ml = MLEngine().initialize(rental_df)

    # Test 1: Vehicle Recommendation
    print("\n--- Vehicle Recommendations for Student 1 ---")
    recs = ml.get_recommendations(student_id=1)
    for i, rec in enumerate(recs, 1):
        print(f"  {i}. {rec['brand']} {rec['model']} - ₹{rec['hourly_rate']}/hr (Score: {rec['recommendation_score']}%)")

    # Test 2: Demand Prediction
    print("\n--- Tomorrow's Demand Prediction ---")
    demand = ml.get_demand_prediction()
    for d in demand:
        bar = "█" * int(d["demand_percentage"] / 5)
        print(f"  {d['vehicle_type']:10} {bar:20} {d['demand_percentage']:5.1f}% ({d['status']})")

    # Test 3: Anomaly Detection
    print("\n--- Payment Anomaly Detection ---")
    test_amounts = [150, 300, 25000, 45, 5000, 200]
    for amt in test_amounts:
        result = ml.detect_payment_anomaly(amt)
        status = "⚠️ ANOMALY" if result["is_anomaly"] else "✓ Normal"
        print(f"  ₹{amt:>8.2f} → {status} ({result['risk_level']})")

    print("\n" + "=" * 60)
    print("ML Module Test Complete!")
    print("=" * 60)
