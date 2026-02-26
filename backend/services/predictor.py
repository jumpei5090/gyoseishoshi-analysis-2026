"""
2026年度 行政書士試験 出題予測エンジン
=============================================
Statistical prediction engine using:
- Linear regression (trend analysis)
- Cycle/periodicity detection
- Bayesian posterior probability
- Recency weighting (exponential decay)
- Gap analysis (years since last appearance)
"""

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict
from models import Question, QuestionTopic, Topic, Law, Subject


MIN_YEAR = 2015
MAX_YEAR = 2024
TARGET_YEAR = 2026
N_YEARS = MAX_YEAR - MIN_YEAR + 1


def _build_topic_timeseries(db: Session):
    """Build a {topic_id: [count_2015, ..., count_2025]} dict."""
    # Get all topic-year counts
    results = (
        db.query(
            QuestionTopic.topic_id,
            Question.year,
            func.count(Question.id).label("cnt"),
        )
        .join(Question, QuestionTopic.question_id == Question.id)
        .filter(Question.year >= MIN_YEAR, Question.year <= MAX_YEAR)
        .group_by(QuestionTopic.topic_id, Question.year)
        .all()
    )

    ts = defaultdict(lambda: [0] * N_YEARS)
    for r in results:
        idx = r.year - MIN_YEAR
        ts[r.topic_id][idx] += r.cnt

    return dict(ts)


def _linear_regression_score(series):
    """
    Fit y = a*x + b. Return predicted value at x=N_YEARS (i.e. 2026).
    Higher slope = upward trend = more likely to appear.
    """
    x = np.arange(N_YEARS, dtype=float)
    y = np.array(series, dtype=float)
    n = len(x)

    if n < 2 or y.sum() == 0:
        return 0.0

    x_mean = x.mean()
    y_mean = y.mean()

    ss_xy = np.sum((x - x_mean) * (y - y_mean))
    ss_xx = np.sum((x - x_mean) ** 2)

    if ss_xx == 0:
        return y_mean

    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean

    predicted = slope * N_YEARS + intercept
    return max(predicted, 0.0)


def _cycle_score(series):
    """
    Detect periodicity: if a topic appears every N years,
    check if 2026 aligns with that cycle.
    Returns a score 0-1.
    """
    appearances = [i for i, v in enumerate(series) if v > 0]
    years_appeared = len(appearances)

    if years_appeared < 2:
        return 0.0

    # Topics that appear every single year → no real "cycle" to detect
    # Use count variance as a proxy for intensity cycling
    if years_appeared >= N_YEARS - 1:
        counts = np.array(series, dtype=float)
        mean_count = counts.mean()
        if mean_count == 0:
            return 0.5
        # Use coefficient of variation: higher CV = more variable intensity
        cv = counts.std() / mean_count
        # Recent trend matters: is the count increasing or stable?
        recent_avg = counts[-3:].mean()
        overall_avg = counts.mean()
        intensity_ratio = min(recent_avg / max(overall_avg, 0.01), 2.0) / 2.0
        return min(0.3 + 0.4 * intensity_ratio + 0.3 * (1.0 - min(cv, 1.0)), 1.0)

    # Calculate gaps between appearances
    gaps = [appearances[i + 1] - appearances[i] for i in range(len(appearances) - 1)]
    if not gaps:
        return 0.0

    avg_gap = np.mean(gaps)
    std_gap = np.std(gaps) if len(gaps) > 1 else avg_gap * 0.5

    last_appearance = appearances[-1]
    # Distance from last appearance year to target year (2026)
    years_since = (TARGET_YEAR - MIN_YEAR) - last_appearance

    if avg_gap == 0:
        return 0.5

    # How close is the current gap to the average cycle?
    cycle_alignment = 1.0 - min(abs(years_since - avg_gap) / max(avg_gap, 1), 1.0)

    # Penalize high variance (less predictable cycles)
    consistency = 1.0 / (1.0 + std_gap)

    return cycle_alignment * consistency


def _recency_score(series, decay=0.3):
    """
    Exponential decay weighting: recent years matter more.
    decay=0.3 means each year back reduces weight by ~26%.
    """
    total = 0.0
    weight_sum = 0.0

    for i, count in enumerate(series):
        w = np.exp(-decay * (N_YEARS - 1 - i))
        total += count * w
        weight_sum += w

    if weight_sum == 0:
        return 0.0

    return total / weight_sum


def _gap_urgency(series):
    """
    Score based on how long since a topic last appeared.
    Topics with moderate gaps (2-4 years) score highest —
    they're "due" but not abandoned.
    Also considers how many questions appeared in the last occurrence.
    """
    appearances = [i for i, v in enumerate(series) if v > 0]

    if not appearances:
        return 0.0

    last = appearances[-1]
    last_year_idx = N_YEARS - 1  # index of 2024 in the series
    gap = last_year_idx - last + 1  # 1 = appeared in 2024
    last_count = series[last]  # how many questions in last appearance
    
    # Base gap score
    if gap <= 1:
        # Appeared in the most recent year - use count intensity
        base = 0.4 + min(last_count / 10.0, 0.2)  # 0.4-0.6
    elif gap == 2:
        base = 0.75   # due for return
    elif gap == 3:
        base = 1.0    # highly due
    elif gap == 4:
        base = 0.9
    elif gap == 5:
        base = 0.7
    else:
        base = max(0.5 - (gap - 6) * 0.1, 0.05)  # long absence

    # Boost for topics that had high counts when they appeared
    avg_count_when_appeared = np.mean([series[i] for i in appearances]) if appearances else 0
    intensity_boost = min(avg_count_when_appeared / 5.0, 0.2)
    
    return min(base + intensity_boost, 1.0)


# 2026 Legal Change Intervention Mapping
# Topics related to the Administrative Scrivener Law revision and Digital Society
INTERVENTION_2026_MAPPING = {
    "行政書士法": 2.5,  # Top priority (Structural Break)
    "情報通信": 1.4,    # Digital Society response
    "個人情報保護": 1.3, # Digital Society response
    "行政不服審査法": 1.25, # Expansion of Specific Scrivener scope
    "地方自治法": 1.15,   # General shift in regional administration
}

GAMMA_FORGETTING = 0.85  # Decaying factor for Bayesian updating


def _get_intervention_boost(topic_name: str) -> float:
    """Return the boost factor for 2026 legal changes."""
    for key, boost in INTERVENTION_2026_MAPPING.items():
        if key in topic_name:
            return boost
    return 1.0


def _bayesian_probability_with_decay(series, prior_alpha=1.0, prior_beta=1.0, boost=1.0):
    """
    Beta-Binomial Bayesian model with Exponential Forgetting (Gamma).
    - Significantly boosts prior for Structural Breaks.
    """
    if boost > 2.0:
        # Extreme boost for Structural Breaks (e.g. Administrative Scrivener Law 2026)
        prior_alpha += 15.0 
    elif boost > 1.0:
        prior_alpha += (boost - 1.0) * 8.0

    decayed_successes = 0.0
    decayed_trials = 0.0
    
    for i, v in enumerate(series):
        weight = GAMMA_FORGETTING ** (N_YEARS - 1 - i)
        if v > 0:
            decayed_successes += weight
        decayed_trials += weight

    posterior_mean = (prior_alpha + decayed_successes) / (prior_alpha + prior_beta + decayed_trials)
    return posterior_mean


def _compute_composite_score(topic_id, topic_name, series):
    """
    Combine all statistical signals into a single prediction score.
    Incorporates 2026 Intervention Effect with stronger weighting for structural breaks.
    """
    trend = _linear_regression_score(series)
    cycle = _cycle_score(series)
    recency = _recency_score(series)
    gap = _gap_urgency(series)
    
    boost = _get_intervention_boost(topic_name)
    bayesian = _bayesian_probability_with_decay(series, boost=boost)

    trend_norm = min(trend / 6.0, 1.0)
    recency_norm = min(recency / 6.0, 1.0)

    # Base weight distribution
    # If structural break (boost > 2), the Bayesian component (prior knowledge) dominates
    if boost > 2.0:
        # Structural break: Ignore historical data mostly, favor the new legal mandate
        score = 0.1 * trend_norm + 0.1 * cycle + 0.1 * recency_norm + 0.1 * gap + 0.6 * bayesian
    else:
        score = 0.25 * trend_norm + 0.20 * cycle + 0.20 * recency_norm + 0.15 * gap + 0.20 * bayesian
    
    # Apply final boost factor
    final_score = score * boost

    return {
        "composite": round(min(final_score * 100, 100), 1),
        "trend": round(trend_norm * 100, 1),
        "cycle": round(cycle * 100, 1),
        "recency": round(recency_norm * 100, 1),
        "gap": round(gap * 100, 1),
        "bayesian": round(bayesian * 100, 1),
        "intervention_boost": boost,
    }


def generate_predictions(db: Session):
    """
    Generate 2026 exam predictions for all topics.
    Returns ranked list grouped by subject and law.
    """
    timeseries = _build_topic_timeseries(db)

    # Get all topics with their hierarchy
    topics = (
        db.query(Topic, Law, Subject)
        .join(Law, Topic.law_id == Law.id)
        .join(Subject, Law.subject_id == Subject.id)
        .order_by(Subject.display_order, Law.id, Topic.id)
        .all()
    )

    predictions = []
    for topic, law, subject in topics:
        series = timeseries.get(topic.id, [0] * N_YEARS)
        total_appearances = sum(series)
        years_appeared = sum(1 for v in series if v > 0)

        scores = _compute_composite_score(topic.id, topic.name, series)

        # Determine trend direction
        x = np.arange(N_YEARS, dtype=float)
        y = np.array(series, dtype=float)
        if y.sum() > 0 and N_YEARS > 1:
            slope = np.polyfit(x, y, 1)[0]
            if slope > 0.05:
                trend_dir = "up"
            elif slope < -0.05:
                trend_dir = "down"
            else:
                trend_dir = "stable"
        else:
            trend_dir = "none"

        # Last appeared year
        appearances = [MIN_YEAR + i for i, v in enumerate(series) if v > 0]
        last_year = appearances[-1] if appearances else None

        predictions.append({
            "topic_id": topic.id,
            "topic_name": topic.name,
            "law_name": law.name,
            "law_id": law.id,
            "subject_name": subject.name,
            "subject_id": subject.id,
            "total_appearances": total_appearances,
            "years_appeared": years_appeared,
            "last_year": last_year,
            "trend_direction": trend_dir,
            "yearly_data": [{"year": MIN_YEAR + i, "count": series[i]} for i in range(N_YEARS)],
            "scores": scores,
        })

    # Sort by composite score descending
    predictions.sort(key=lambda p: p["scores"]["composite"], reverse=True)

    # Add rank
    for i, p in enumerate(predictions):
        p["rank"] = i + 1

    return predictions


def generate_subject_predictions(db: Session):
    """
    Generate subject-level (law-level) predictions.
    Aggregate topic scores for each law.
    """
    topic_predictions = generate_predictions(db)

    # Group by law
    law_groups = defaultdict(list)
    for p in topic_predictions:
        key = (p["subject_id"], p["subject_name"], p["law_id"], p["law_name"])
        law_groups[key].append(p)

    law_predictions = []
    for (subj_id, subj_name, law_id, law_name), topics in law_groups.items():
        if not topics:
            continue

        avg_score = np.mean([t["scores"]["composite"] for t in topics])
        max_score = max(t["scores"]["composite"] for t in topics)
        total_q = sum(t["total_appearances"] for t in topics)

        # Top 3 topics for this law
        top_topics = sorted(topics, key=lambda t: t["scores"]["composite"], reverse=True)[:3]

        law_predictions.append({
            "subject_id": subj_id,
            "subject_name": subj_name,
            "law_id": law_id,
            "law_name": law_name,
            "avg_score": round(avg_score, 1),
            "max_score": round(max_score, 1),
            "total_questions": total_q,
            "topic_count": len(topics),
            "top_topics": [
                {
                    "name": t["topic_name"],
                    "score": t["scores"]["composite"],
                    "trend": t["trend_direction"],
                    "last_year": t["last_year"],
                }
                for t in top_topics
            ],
        })

    law_predictions.sort(key=lambda p: p["max_score"], reverse=True)
    for i, p in enumerate(law_predictions):
        p["rank"] = i + 1

    return law_predictions
