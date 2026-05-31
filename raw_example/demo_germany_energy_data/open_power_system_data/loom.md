source: https://data.open-power-system-data.org/time_series/2020-10-06/
source: https://data.open-power-system-data.org/national_generation_capacity/2020-10-01/

# Open Power System Data Extracts

These files are small extracts from Open Power System Data packages:

- `time_series/germany_2015_new_year_day_power.csv` comes from the OPSD
  time-series package version 2020-10-06, hourly single-index file.
- `generation_capacity/germany_2015_net_capacity.csv` comes from the OPSD
  national generation capacity package version 2020-10-01.

Human annotation:

The 24-hour time-series slice keeps original OPSD-style fields for German load,
solar generation, wind generation, and related capacity/profile values. The
capacity table keeps Germany, year 2015, `ENTSO-E SOAF`, net-capacity rows for
common generation categories. The first seven solar generation values are empty
in the raw OPSD extract, which is useful for demonstrating how a modeling agent
must notice missing values before using the file.
