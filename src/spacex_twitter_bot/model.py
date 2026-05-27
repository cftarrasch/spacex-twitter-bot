from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .features import CATEGORICAL_FEATURES, NUMERIC_FEATURES, extract_feature_row


@dataclass(frozen=True)
class TargetSpec:
    name: str
    label_getter: Any


def build_pipeline() -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "classifier",
                LogisticRegression(max_iter=1000, class_weight="balanced"),
            ),
        ]
    )


def build_training_frame(
    launches: list[dict[str, Any]], label_getter: Any
) -> tuple[pd.DataFrame, pd.Series]:
    rows: list[dict[str, Any]] = []
    labels: list[bool] = []
    for launch in launches:
        label = label_getter(launch)
        if label is None:
            continue
        rows.append(extract_feature_row(launch))
        labels.append(label)
    return pd.DataFrame(rows), pd.Series(labels, name="target")


def train_classifier(
    launches: list[dict[str, Any]], spec: TargetSpec
) -> dict[str, Any]:
    x, y = build_training_frame(launches, spec.label_getter)
    if len(y) < 10:
        raise RuntimeError(f"Not enough rows to train {spec.name}: {len(y)}")
    if y.nunique() < 2:
        raise RuntimeError(f"Target {spec.name} has only one class")

    pipeline = build_pipeline()
    metrics: dict[str, Any] = {
        "sample_count": int(len(y)),
        "positive_rate": float(y.mean()),
    }

    class_counts = y.value_counts()
    can_stratify = class_counts.min() >= 2 and len(y) >= 20
    if can_stratify:
        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=0.25, random_state=42, stratify=y
        )
        pipeline.fit(x_train, y_train)
        predicted = pipeline.predict(x_test)
        metrics["holdout_accuracy"] = float(accuracy_score(y_test, predicted))
        if y_test.nunique() == 2:
            probabilities = probability_for_true(pipeline, x_test)
            metrics["holdout_roc_auc"] = float(roc_auc_score(y_test, probabilities))
    pipeline.fit(x, y)
    return {
        "target": spec.name,
        "pipeline": pipeline,
        "metrics": metrics,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
    }


def probability_for_true(pipeline: Pipeline, rows: pd.DataFrame) -> list[float]:
    classes = list(pipeline.classes_)
    try:
        true_index = classes.index(True)
    except ValueError:
        true_index = 1
    probabilities = pipeline.predict_proba(rows)
    return [float(row[true_index]) for row in probabilities]


def train_model_bundle(launches: list[dict[str, Any]]) -> dict[str, Any]:
    from .features import landing_success_label, launch_success_label

    return {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "source": "https://api.spacexdata.com/v4",
        "models": {
            "launch_success": train_classifier(
                launches, TargetSpec("launch_success", launch_success_label)
            ),
            "landing_success": train_classifier(
                launches, TargetSpec("landing_success", landing_success_label)
            ),
        },
    }


def save_model_bundle(bundle: dict[str, Any], model_path: Path) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path)


def load_model_bundle(model_path: Path) -> dict[str, Any]:
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found at {model_path}. Run training first."
        )
    return joblib.load(model_path)


def predict_probabilities(
    bundle: dict[str, Any], launch: dict[str, Any]
) -> dict[str, float]:
    row = pd.DataFrame([extract_feature_row(launch)])
    predictions: dict[str, float] = {}
    for name, model_info in bundle["models"].items():
        predictions[name] = probability_for_true(model_info["pipeline"], row)[0]
    return predictions
