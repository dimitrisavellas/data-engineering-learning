import sys

import pandas as pd

print(f"Arguments: {sys.argv}")

month = sys.argv[1]
print(f"Running pipeline for month {month}")

df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

df.to_parquet(f"output_day_{sys.argv[1]}.parquet")
