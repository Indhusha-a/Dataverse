"""Phases 9-12: leakage-safe preprocessing + fare model + duration model.
Run with `python -m src.modeling` (trains and saves both)."""
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from src.config import MODELS_DIR, OUTPUTS_DIR, RANDOM_SEED
from src.splits import save_split, load_split_frames

NUMERIC = ["distance_miles", "rider_count", "pickup_hour", "pickup_dow", "pickup_month"]
CATEGORICAL = ["pickup_zone", "dropoff_zone"]
MAX_TRAIN_ROWS = 4_000_000  # train is ~34.7M rows; SimpleImputer's median sort OOMs above a few million


def build_preprocessor(numeric_features, categorical_features):
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore", max_categories=40, sparse_output=False)),
    ])
    return ColumnTransformer([
        ("num", numeric_pipe, numeric_features),
        ("cat", categorical_pipe, categorical_features),
    ])


def add_common_features(df):
    df = df.copy()
    df["pickup_hour"] = df["pickup_timestamp"].dt.hour
    df["pickup_dow"] = df["pickup_timestamp"].dt.dayofweek
    df["pickup_month"] = df["pickup_timestamp"].dt.month
    df["pickup_zone"] = df["origin_loc_id"].astype(str)
    df["dropoff_zone"] = df["dest_loc_id"].astype(str)
    return df


def add_duration_target(df):
    df = df.copy()
    df["trip_duration_minutes"] = (df["dropoff_timestamp"] - df["pickup_timestamp"]).dt.total_seconds() / 60
    return df


def fresh_candidates():
    """A new dict of unfitted estimators each call -- keeps the fare and duration
    runs from ever sharing a fitted estimator instance."""
    return {
        "baseline_mean": DummyRegressor(strategy="mean"),
        "ridge": Ridge(random_state=RANDOM_SEED),
        "random_forest": RandomForestRegressor(n_estimators=200, max_depth=12, random_state=RANDOM_SEED, n_jobs=-1),
        "hist_gbm": HistGradientBoostingRegressor(random_state=RANDOM_SEED),
    }


def train_compare_and_save(task_name, target_col, load_columns, prep_fn, metrics_filename, model_filename):
    frames = load_split_frames(columns=load_columns)
    frames = {k: prep_fn(v).dropna(subset=[target_col]) for k, v in frames.items()}
    Xy = {k: (v[NUMERIC + CATEGORICAL], v[target_col]) for k, v in frames.items()}
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = Xy["train"], Xy["validation"], Xy["test"]

    if len(X_train) > MAX_TRAIN_ROWS:
        X_train = X_train.sample(n=MAX_TRAIN_ROWS, random_state=RANDOM_SEED)
        y_train = y_train.loc[X_train.index]

    rows, fitted = [], {}
    for name, est in fresh_candidates().items():
        print(f"[{task_name}] fitting {name} on {len(X_train):,} rows...")
        pipe = Pipeline([("prep", build_preprocessor(NUMERIC, CATEGORICAL)), ("model", est)])
        pipe.fit(X_train, y_train)                 # preprocessing is fit here, on TRAIN only
        pred = pipe.predict(X_val)                 # validation only ever gets .transform()
        mae = mean_absolute_error(y_val, pred)
        rows.append({"model": name, "split": "validation",
                     "MAE": mae,
                     "RMSE": root_mean_squared_error(y_val, pred),
                     "R2": r2_score(y_val, pred)})
        fitted[name] = pipe
        print(f"[{task_name}] {name} done, validation MAE={mae:.4f}")

    best_name = min(rows, key=lambda r: r["MAE"])["model"]
    best_pipe = fitted[best_name]

    # Focused tuning of the single strongest candidate only (SS35) -- not a grid over all four.
    if best_name == "hist_gbm":
        search = RandomizedSearchCV(
            best_pipe, param_distributions={"model__max_depth": [4, 6, 8, None],
                                             "model__learning_rate": [0.03, 0.06, 0.1]},
            n_iter=6, cv=3, scoring="neg_mean_absolute_error", random_state=RANDOM_SEED)
        search.fit(X_train, y_train)
        best_pipe = search.best_estimator_

    # Final test evaluation happens exactly once, after model selection is locked in.
    test_pred = best_pipe.predict(X_test)
    rows.append({"model": best_name + "_FINAL", "split": "test",
                 "MAE": mean_absolute_error(y_test, test_pred),
                 "RMSE": root_mean_squared_error(y_test, test_pred),
                 "R2": r2_score(y_test, test_pred)})

    OUTPUTS_DIR.joinpath("metrics").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUTS_DIR / "metrics" / metrics_filename, index=False)
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(best_pipe, MODELS_DIR / model_filename)
    print(f"[{task_name}] best model: {best_name} -> models/{model_filename}")


def run_fare():
    """PDF 2.1 -- predict base_fare before a trip starts."""
    train_compare_and_save(
        task_name="fare", target_col="base_fare",
        load_columns=["pickup_timestamp", "distance_miles", "rider_count",
                      "origin_loc_id", "dest_loc_id", "base_fare"],
        prep_fn=add_common_features,
        metrics_filename="fare_model_comparison.csv", model_filename="fare_model.pkl",
    )


def run_duration():
    """PDF 2.2 -- predict total trip time in minutes."""
    train_compare_and_save(
        task_name="duration", target_col="trip_duration_minutes",
        load_columns=["pickup_timestamp", "dropoff_timestamp", "distance_miles", "rider_count",
                      "origin_loc_id", "dest_loc_id"],
        prep_fn=lambda df: add_duration_target(add_common_features(df)),
        metrics_filename="duration_model_comparison.csv", model_filename="duration_model.pkl",
    )
    # dropoff_timestamp and trip_duration_minutes itself are never in NUMERIC/CATEGORICAL
    # above -- confirm that stays true if you ever edit the feature lists (Activity.md SS16).


if __name__ == "__main__":
    save_split()
    run_fare()
    run_duration()