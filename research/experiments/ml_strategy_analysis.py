"""
Offline ML analysis tools for Optuna strategy results.

This module loads Optuna result CSVs and provides simple modeling and clustering
utilities to explore relationships between strategy parameters and objective
performance.
"""
from __future__ import annotations

import argparse
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score


def _load_numeric_features(csv_path: str) -> tuple[pd.DataFrame, pd.Series]:
    """Load CSV and return numeric features with objective_value as target."""
    df = pd.read_csv(csv_path)
    if "objective_value" not in df.columns:
        raise ValueError("CSV must contain an 'objective_value' column")

    numeric_df = df.select_dtypes(include=[np.number]).copy()
    if numeric_df.empty:
        raise ValueError("No numeric columns found for modeling")

    y = numeric_df.pop("objective_value")
    if y.isnull().all():
        raise ValueError("Target column 'objective_value' contains only NaNs")

    X = numeric_df.fillna(numeric_df.median())
    return X, y


def _print_feature_importance(features: Iterable[str], importances: Iterable[float]) -> None:
    print("Feature importances:")
    for name, importance in sorted(zip(features, importances), key=lambda pair: pair[1], reverse=True):
        print(f"  {name}: {importance:.4f}")


def train_performance_model(csv_path: str):
    """
    Load the CSV, train a simple regression model predicting objective_value from strategy parameters and metrics.
    Print feature importances or equivalent diagnostic output.
    Return the fitted model.
    """
    X, y = _load_numeric_features(csv_path)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    r2 = r2_score(y_test, predictions)
    print(f"Trained RandomForestRegressor on {len(X_train)} samples; R^2 on hold-out: {r2:.4f}")
    _print_feature_importance(X.columns, model.feature_importances_)

    return model


def cluster_strategies(csv_path: str, n_clusters: int = 3):
    """
    Cluster strategies based on parameters and performance metrics.
    Print summary info for each cluster (e.g. average objective_value and parameter ranges).
    """
    X, y = _load_numeric_features(csv_path)

    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = kmeans.fit_predict(X)

    df = X.copy()
    df["objective_value"] = y
    df["cluster"] = labels

    print(f"Clustered {len(df)} strategies into {n_clusters} groups.")
    for cluster_id, cluster_df in df.groupby("cluster"):
        print(f"\nCluster {cluster_id}:")
        print(f"  Size: {len(cluster_df)}")
        print(f"  Avg objective_value: {cluster_df['objective_value'].mean():.4f}")

        param_ranges = {}
        for col in X.columns:
            col_min = cluster_df[col].min()
            col_max = cluster_df[col].max()
            col_mean = cluster_df[col].mean()
            param_ranges[col] = (col_min, col_max, col_mean)

        for col, (col_min, col_max, col_mean) in param_ranges.items():
            print(f"  {col}: min={col_min:.4f}, max={col_max:.4f}, mean={col_mean:.4f}")

    return kmeans


def main():
    parser = argparse.ArgumentParser(description="Offline ML analysis for Optuna strategy results")
    parser.add_argument("--csv", required=True, help="Path to Optuna results CSV (e.g., reports/optuna_ma_AAPL.csv)")
    parser.add_argument(
        "--clusters",
        type=int,
        default=3,
        help="Number of clusters to identify; set to 0 to skip clustering",
    )
    args = parser.parse_args()

    train_performance_model(args.csv)

    if args.clusters and args.clusters > 0:
        cluster_strategies(args.csv, n_clusters=args.clusters)


if __name__ == "__main__":
    main()
