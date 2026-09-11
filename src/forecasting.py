"""Phase 13: demand forecasting for top taxi zones. Run with `python -m src.forecasting`."""
import joblib
import pandas as pd
import matplotlib.pyplot as plt
from src.config import PROCESSED_DIR, OUTPUTS_DIR, MODELS_DIR
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

def build_hourly_demand(top_n_zones=10):
    frames = [pd.read_parquet(p, columns=["pickup_timestamp", "origin_loc_id"])
              for p in sorted(PROCESSED_DIR.glob("*.parquet"))]
    df = pd.concat(frames, ignore_index=True)
    top_zones = df["origin_loc_id"].value_counts().head(top_n_zones).index
    df = df[df["origin_loc_id"].isin(top_zones)]
    df["hour_bucket"] = df["pickup_timestamp"].dt.floor("h")
    hourly = (df.groupby(["origin_loc_id", "hour_bucket"]).size()
                .rename("pickups").reset_index())
    # fill missing hours with 0 so lag/rolling windows sit on a complete, regular grid
    filled = []
    for zone, g in hourly.groupby("origin_loc_id"):
        idx = pd.date_range(g["hour_bucket"].min(), g["hour_bucket"].max(), freq="h")
        s = g.set_index("hour_bucket")["pickups"].reindex(idx, fill_value=0)
        s.index.name = "hour_bucket"
        filled.append(s.rename("pickups").reset_index().assign(origin_loc_id=zone))
    return pd.concat(filled, ignore_index=True)

def add_lag_rolling_features(df):
    df = df.sort_values(["origin_loc_id", "hour_bucket"]).copy()
    g = df.groupby("origin_loc_id")["pickups"]
    for lag in [1, 2, 3, 24, 48, 168]:
        df[f"lag_{lag}"] = g.shift(lag)                       # value at T-lag, never T or later
    # shift(1) BEFORE rolling so the window for row T covers T-1 back to T-24, excluding T itself
    df["rolling_mean_24"] = g.shift(1).rolling(24).mean()
    df["rolling_mean_168"] = g.shift(1).rolling(168).mean()
    df["hour"] = df["hour_bucket"].dt.hour
    df["dow"] = df["hour_bucket"].dt.dayofweek
    df["month"] = df["hour_bucket"].dt.month
    df["is_weekend"] = df["dow"].isin([5, 6]).astype(int)
    return df.dropna()  # drops the first 168h per zone where lag_168 isn't available yet

def chronological_split(df, val_days=14, test_days=7):
    cutoff_test = df["hour_bucket"].max() - pd.Timedelta(days=test_days)
    cutoff_val = cutoff_test - pd.Timedelta(days=val_days)
    return (df[df["hour_bucket"] < cutoff_val],
            df[(df["hour_bucket"] >= cutoff_val) & (df["hour_bucket"] < cutoff_test)],
            df[df["hour_bucket"] >= cutoff_test])

FEATURES = ["lag_1","lag_2","lag_3","lag_24","lag_48","lag_168",
            "rolling_mean_24","rolling_mean_168","hour","dow","month","is_weekend"]

def recursive_forecast(model, zone_history, horizon_hours=72):
    """zone_history: raw hourly pickups for ONE zone (from build_hourly_demand),
    sorted ascending. Forecasts horizon_hours steps past the last known hour by
    feeding each prediction back in as the next step's lag_1/lag_2/... -- the
    only way to get real future values, since lag_1..lag_3 don't exist yet for
    anything past the first couple of forecasted hours."""
    series = zone_history.set_index("hour_bucket")["pickups"].sort_index().copy()
    last_hour = series.index.max()
    preds = []
    for h in range(1, horizon_hours + 1):
        target_hour = last_hour + pd.Timedelta(hours=h)
        row = {
            "lag_1": series.iloc[-1], "lag_2": series.iloc[-2], "lag_3": series.iloc[-3],
            "lag_24": series.iloc[-24], "lag_48": series.iloc[-48], "lag_168": series.iloc[-168],
            "rolling_mean_24": series.iloc[-24:].mean(), "rolling_mean_168": series.iloc[-168:].mean(),
            "hour": target_hour.hour, "dow": target_hour.dayofweek, "month": target_hour.month,
            "is_weekend": int(target_hour.dayofweek in (5, 6)),
        }
        pred = max(0.0, model.predict(pd.DataFrame([row])[FEATURES])[0])
        preds.append({"hour_bucket": target_hour, "predicted_pickups": pred})
        series.loc[target_hour] = pred
    return pd.DataFrame(preds)

def generate_forward_forecasts(model, hourly, horizons=(24, 48, 72)):
    max_horizon = max(horizons)
    per_zone = []
    for zone, g in hourly.groupby("origin_loc_id"):
        fc = recursive_forecast(model, g, horizon_hours=max_horizon)
        fc["origin_loc_id"] = zone
        per_zone.append(fc)
    full = pd.concat(per_zone, ignore_index=True)
    for h in horizons:
        full.groupby("origin_loc_id").head(h).to_csv(
            OUTPUTS_DIR / "forecasts" / f"demand_forecast_{h}h.csv", index=False)
    return full

def plot_example_zone(test, test_pred, forecasts, zone_id):
    hist = test[test["origin_loc_id"] == zone_id].sort_values("hour_bucket")
    hist_pred = test_pred[test["origin_loc_id"] == zone_id]
    future = forecasts[forecasts["origin_loc_id"] == zone_id].sort_values("hour_bucket")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(hist["hour_bucket"], hist["pickups"], label="Actual (test period)")
    ax.plot(hist["hour_bucket"], hist_pred, label="Predicted (test period)", linestyle="--")
    ax.plot(future["hour_bucket"], future["predicted_pickups"], label="Forward 72h forecast", linestyle=":")
    ax.set_title(f"Zone {zone_id}: hourly pickups, actual vs. predicted vs. forward forecast")
    ax.set_xlabel("Hour"); ax.set_ylabel("Pickup count")
    ax.legend()
    fig.autofmt_xdate()
    fig.savefig(OUTPUTS_DIR / "figures" / "demand_forecast_example.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

def run():
    hourly = build_hourly_demand()
    feat = add_lag_rolling_features(hourly)
    train, val, test = chronological_split(feat)

    model = HistGradientBoostingRegressor(random_state=42)
    model.fit(train[FEATURES], train["pickups"])
    val_pred = model.predict(val[FEATURES])
    val_mae, val_rmse = mean_absolute_error(val["pickups"], val_pred), root_mean_squared_error(val["pickups"], val_pred)
    print("Validation MAE:", val_mae)
    print("Validation RMSE:", val_rmse)

    test_pred = model.predict(test[FEATURES])
    test_mae, test_rmse = mean_absolute_error(test["pickups"], test_pred), root_mean_squared_error(test["pickups"], test_pred)
    print("Final TEST MAE:", test_mae)
    print("Final TEST RMSE:", test_rmse)

    OUTPUTS_DIR.joinpath("metrics").mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"model": "hist_gbm", "split": "validation", "MAE": val_mae, "RMSE": val_rmse},
        {"model": "hist_gbm_FINAL", "split": "test", "MAE": test_mae, "RMSE": test_rmse},
    ]).to_csv(OUTPUTS_DIR / "metrics" / "demand_model_comparison.csv", index=False)

    OUTPUTS_DIR.joinpath("forecasts").mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.joinpath("figures").mkdir(parents=True, exist_ok=True)
    test.assign(predicted=test_pred).to_csv(OUTPUTS_DIR / "forecasts" / "demand_test_predictions.csv", index=False)
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODELS_DIR / "demand_model.pkl")

    # Refit on all available history for the actual forward-looking forecast --
    # test rows are now "past" relative to the true unknown future, so this doesn't
    # touch the validation/test metrics already reported above.
    final_model = HistGradientBoostingRegressor(random_state=42)
    final_model.fit(feat[FEATURES], feat["pickups"])
    forecasts = generate_forward_forecasts(final_model, hourly)

    example_zone = hourly["origin_loc_id"].value_counts().index[0]
    plot_example_zone(test, test_pred, forecasts, example_zone)
    print("Saved 24/48/72h forecasts to outputs/forecasts/ and a plot to outputs/figures/")

if __name__ == "__main__":
    run()
