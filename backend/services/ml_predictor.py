"""
Machine Learning Based Exam Prediction Service
=============================================
Uses scikit-learn (Random Forest) to predict 2026 exam topics.
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from models import Question, QuestionTopic, Topic, Law, Subject

MIN_YEAR = 2015
MAX_YEAR = 2025
TARGET_YEAR = 2026
N_YEARS = MAX_YEAR - MIN_YEAR + 1

class MLPredictor:
    def __init__(self, db: Session):
        self.db = db
        self.model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
        self.le_subject = LabelEncoder()
        self.le_law = LabelEncoder()
        
    def _fetch_all_data(self):
        """Fetch all topic-year counts from DB."""
        results = (
            self.db.query(
                QuestionTopic.topic_id,
                Question.year,
                func.count(Question.id).label("cnt"),
            )
            .join(Question, QuestionTopic.question_id == Question.id)
            .filter(Question.year >= MIN_YEAR, Question.year <= MAX_YEAR)
            .group_by(QuestionTopic.topic_id, Question.year)
            .all()
        )
        
        # Build 2D array [topic_id][year_offset]
        ts = defaultdict(lambda: [0] * N_YEARS)
        for r in results:
            idx = r.year - MIN_YEAR
            ts[r.topic_id][idx] += r.cnt
        return ts

    def extract_features(self, topic_id, year_at, ts_data, subjects_map, laws_map):
        """
        Extract numerical features for a topic at a specific year point.
        year_at is the index in the timeseries (0 for 2015, 10 for 2025).
        We use data UP TO year_at-1 to predict year_at.
        """
        series = ts_data[topic_id][:year_at]
        if not series:
            return None
        
        # 1. Historical counts
        total_q = sum(series)
        avg_q = np.mean(series)
        
        # 2. Appearance flags
        appearances = [i for i, v in enumerate(series) if v > 0]
        years_since_last = (year_at - 1 - appearances[-1]) if appearances else 15
        
        # 3. Trend (Slope)
        if len(series) >= 2:
            x = np.arange(len(series))
            slope = np.polyfit(x, series, 1)[0]
        else:
            slope = 0
            
        # 4. Binary recency (1 if appeared in last 2 years)
        appeared_last_2 = 1 if (year_at - 1 - appearances[-1] < 2 if appearances else False) else 0
        
        # 5. Category info
        subj_id = subjects_map.get(topic_id, 0)
        law_id = laws_map.get(topic_id, 0)
        
        return [
            total_q, avg_q, years_since_last, slope, 
            appeared_last_2, subj_id, law_id
        ]

    def train(self):
        """Build dataset and train the model."""
        ts = self._fetch_all_data()
        topics = self.db.query(Topic, Law).join(Law).all()
        
        subjects_map = {t.Topic.id: t.Law.subject_id for t in topics}
        laws_map = {t.Topic.id: t.Law.id for t in topics}
        
        X = []
        y = []
        
        # Rolling window training: predict 2020 using 2015-2019, etc.
        # Start from year_idx 5 (2020) to have enough history
        for year_idx in range(5, N_YEARS):
            actual_year = MIN_YEAR + year_idx
            for topic_id in ts.keys():
                features = self.extract_features(topic_id, year_idx, ts, subjects_map, laws_map)
                if features:
                    X.append(features)
                    # Label: did it appear in this year?
                    y.append(1 if ts[topic_id][year_idx] > 0 else 0)
        
        if X:
            self.model.fit(X, y)
            print(f"Model trained on {len(X)} samples.")
        else:
            print("Not enough data to train model.")

    def predict_2026(self):
        """Predict probability for 2026."""
        ts = self._fetch_all_data()
        topics = (
            self.db.query(Topic, Law, Subject)
            .join(Law, Topic.law_id == Law.id)
            .join(Subject, Law.subject_id == Subject.id)
            .all()
        )
        
        subjects_map = {t.Topic.id: t.Law.subject_id for t in topics}
        laws_map = {t.Topic.id: t.Law.id for t in topics}
        
        results = []
        # Predict 2026 (index N_YEARS)
        for t in topics:
            topic_id = t.Topic.id
            # Use ALL data up to 2025 (index 10)
            features = self.extract_features(topic_id, N_YEARS, ts, subjects_map, laws_map)
            if features:
                # Predict probability [prob_0, prob_1]
                prob = self.model.predict_proba([features])[0][1]
                
                # Feature importance (top values for this specific prediction)
                # For simplicity, we just use the global importance
                
                results.append({
                    "topic_id": topic_id,
                    "topic_name": t.Topic.name,
                    "law_name": t.Law.name,
                    "subject_name": t.Subject.name,
                    "ml_score": round(prob * 100, 1),
                    "features": {
                        "years_since_last": features[2],
                        "trend_slope": round(features[3], 3),
                        "total_appearances": features[0]
                    }
                })
        
        results.sort(key=lambda x: x["ml_score"], reverse=True)
        return results

    def get_feature_importance(self):
        """Return global feature importance."""
        feature_names = [
            "Total Appearances", "Avg Questions/Year", "Years Since Last", 
            "Trend Slope", "Appeared in Last 2Y", "Subject ID", "Law ID"
        ]
        importances = self.model.feature_importances_
        return sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)

def generate_ml_predictions(db: Session):
    predictor = MLPredictor(db)
    predictor.train()
    return predictor.predict_2026()
