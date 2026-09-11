"""Phase 14: hotspots, OD flows, and zone-demand clustering. Run with `python -m src.spatial`."""
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from src.config import PROCESSED_DIR, OUTPUTS_DIR, ZONE_FILE

def cluster_zone_demand_patterns(df, n_clusters=4, min_trips=100):
    """PDF 3.2 -- cluster zones by their normalized hourly pickup profile, so zones
    with similar temporal behaviour (morning-commuter vs. night-life vs. steady
    all-day, etc.) group together. Purely descriptive/unsupervised."""
    hour = df["pickup_timestamp"].dt.hour
    profile = df.assign(hour=hour).groupby(["origin_loc_id", "hour"]).size().unstack(fill_value=0)
    totals = profile.sum(axis=1)
    profile_norm = profile.div(totals, axis=0)  # each zone's 24-hour shape, independent of volume

    eligible = profile_norm[totals >= min_trips]
    X = StandardScaler().fit_transform(eligible.values)
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(X)

    result = pd.DataFrame({"origin_loc_id": eligible.index, "total_pickups": totals.loc[eligible.index].values,
                            "cluster": labels})
    return result, profile_norm

def plot_cluster_profiles(profile_norm, result, n_clusters=4):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for c in range(n_clusters):
        zone_ids = result.loc[result["cluster"] == c, "origin_loc_id"]
        avg_profile = profile_norm.loc[zone_ids].mean()
        ax.plot(avg_profile.index, avg_profile.values, marker="o", markersize=3,
                label=f"Cluster {c} (n={len(zone_ids)} zones)")
    ax.set_title("Average hourly pickup share by zone cluster")
    ax.set_xlabel("Hour of day"); ax.set_ylabel("Share of that zone's daily pickups")
    ax.legend()
    fig.savefig(OUTPUTS_DIR / "figures" / "zone_clusters.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

def run():
    zones = pd.read_csv(ZONE_FILE)
    frames = [pd.read_parquet(p, columns=["pickup_timestamp", "origin_loc_id", "dest_loc_id"])
              for p in sorted(PROCESSED_DIR.glob("*.parquet"))]
    df = pd.concat(frames, ignore_index=True)

    top_pickups = (df["origin_loc_id"].value_counts().head(15).rename_axis("loc_id")
                   .reset_index(name="pickup_count").merge(zones, on="loc_id"))
    top_dropoffs = (df["dest_loc_id"].value_counts().head(15).rename_axis("loc_id")
                    .reset_index(name="dropoff_count").merge(zones, on="loc_id"))
    od_pairs = (df.groupby(["origin_loc_id", "dest_loc_id"]).size()
                .rename("trip_count").reset_index()
                .sort_values("trip_count", ascending=False).head(20))
    od_pairs = (od_pairs.merge(zones, left_on="origin_loc_id", right_on="loc_id")
                .rename(columns={"zone_name": "origin_zone"})
                .merge(zones, left_on="dest_loc_id", right_on="loc_id", suffixes=("", "_d"))
                .rename(columns={"zone_name": "dest_zone"}))

    cluster_result, profile_norm = cluster_zone_demand_patterns(df)
    cluster_result = cluster_result.merge(zones, left_on="origin_loc_id", right_on="loc_id", how="left")
    plot_cluster_profiles(profile_norm, cluster_result)

    OUTPUTS_DIR.joinpath("tables").mkdir(parents=True, exist_ok=True)
    top_pickups.to_csv(OUTPUTS_DIR / "tables" / "top_pickup_zones.csv", index=False)
    top_dropoffs.to_csv(OUTPUTS_DIR / "tables" / "top_dropoff_zones.csv", index=False)
    od_pairs.to_csv(OUTPUTS_DIR / "tables" / "top_od_pairs.csv", index=False)
    cluster_result.to_csv(OUTPUTS_DIR / "tables" / "zone_clusters.csv", index=False)
    print("Saved top_pickup_zones.csv, top_dropoff_zones.csv, top_od_pairs.csv, zone_clusters.csv, zone_clusters.png")

if __name__ == "__main__":
    run()