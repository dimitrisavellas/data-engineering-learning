from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

DATA_DIR = Path(__file__).parent / "data"


def write_table(df: pd.DataFrame, table: str, engine) -> None:
    df.to_sql(name=table, con=engine, if_exists="replace", index=False)
    print(f"{table}: {len(df)} rows")


def main() -> None:
    engine = create_engine("postgresql://root:root@localhost:5432/data_homework")

    trips = pd.read_parquet(DATA_DIR / "green_tripdata_2025-11.parquet")
    zones = pd.read_csv(DATA_DIR / "taxi_zone_lookup.csv")

    write_table(trips, "green_taxi_trips", engine)
    write_table(zones, "zones", engine)


if __name__ == "__main__":
    main()
