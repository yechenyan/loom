from __future__ import annotations


TUTORIAL_DATASET_NAME = "demo_germany_energy_data"

TUTORIAL_FILES = {
    "loom.md": """source: https://data.open-power-system-data.org/time_series/2020-10-06/
source: https://data.open-power-system-data.org/national_generation_capacity/2020-10-01/
source: https://www.ise.fraunhofer.de/en/press-media/press-releases/2025/public-electricity-generation-2024-renewable-energies-cover-more-than-60-percent-of-german-electricity-consumption-for-the-first-time.html
source: https://www.bundesregierung.de/breg-de/schwerpunkte/klimaschutz/climate-change-act-2021-1913970

# Germany Energy Data Library

This raw example is a small data library for Germany energy-modeling demos.
It intentionally avoids model topology, scenario design, and derived model
inputs. Agents can use Loom to find the facts they need, then decide later how
to build a national, regional, city, or community-scale model.

Contents:

- `open_power_system_data/`: public German power-system time-series and
  installed-capacity extracts from OPSD.
- `fraunhofer_energy_charts/`: selected German 2024 public electricity-system
  context from Fraunhofer ISE Energy-Charts.
- `german_climate_policy/`: selected German climate-policy targets.

Human annotation:

The dataset is deliberately compact so Loom scans are easy to review by hand.
The files are source extracts and notes, not authoritative planning datasets
and not a complete model. For example, an agent could combine the OPSD hourly
load/wind/solar extract with OPSD capacity rows to test a tiny residual-load
calculation, but that calculation should live outside `raw_example`.
""",
    "open_power_system_data/loom.md": """source: https://data.open-power-system-data.org/time_series/2020-10-06/
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
""",
    "open_power_system_data/time_series/germany_2015_new_year_day_power.csv": """utc_timestamp,cet_cest_timestamp,DE_load_actual_entsoe_transparency,DE_solar_capacity,DE_solar_generation_actual,DE_solar_profile,DE_wind_capacity,DE_wind_generation_actual,DE_wind_profile,DE_wind_offshore_generation_actual,DE_wind_onshore_generation_actual
2015-01-01T00:00:00Z,2015-01-01T01:00:00+0100,41151.0000,37248.0000,,,27913.0000,8852.0000,0.3171,517.0000,8336.0000
2015-01-01T01:00:00Z,2015-01-01T02:00:00+0100,40135.0000,37248.0000,,,27913.0000,9054.0000,0.3244,514.0000,8540.0000
2015-01-01T02:00:00Z,2015-01-01T03:00:00+0100,39106.0000,37248.0000,,,27913.0000,9070.0000,0.3249,518.0000,8552.0000
2015-01-01T03:00:00Z,2015-01-01T04:00:00+0100,38765.0000,37248.0000,,,27913.0000,9163.0000,0.3283,520.0000,8643.0000
2015-01-01T04:00:00Z,2015-01-01T05:00:00+0100,38941.0000,37248.0000,,,27913.0000,9231.0000,0.3307,520.0000,8712.0000
2015-01-01T05:00:00Z,2015-01-01T06:00:00+0100,39045.0000,37248.0000,,,27913.0000,9689.0000,0.3471,521.0000,9167.0000
2015-01-01T06:00:00Z,2015-01-01T07:00:00+0100,40206.0000,37248.0000,,,27913.0000,10331.0000,0.3701,520.0000,9811.0000
2015-01-01T07:00:00Z,2015-01-01T08:00:00+0100,41133.0000,37248.0000,71.0000,0.0019,27913.0000,10208.0000,0.3657,525.0000,9683.0000
2015-01-01T08:00:00Z,2015-01-01T09:00:00+0100,42963.0000,37248.0000,773.0000,0.0207,27913.0000,10029.0000,0.3593,527.0000,9502.0000
2015-01-01T09:00:00Z,2015-01-01T10:00:00+0100,45088.0000,37248.0000,2117.0000,0.0568,27913.0000,10550.0000,0.3780,525.0000,10025.0000
2015-01-01T10:00:00Z,2015-01-01T11:00:00+0100,47013.0000,37248.0000,3364.0000,0.0903,27913.0000,11390.0000,0.4080,528.0000,10862.0000
2015-01-01T11:00:00Z,2015-01-01T12:00:00+0100,48159.0000,37248.0000,4198.0000,0.1127,27913.0000,12103.0000,0.4336,528.0000,11575.0000
2015-01-01T12:00:00Z,2015-01-01T13:00:00+0100,47164.0000,37248.0000,3500.0000,0.0940,27913.0000,12505.0000,0.4480,528.0000,11977.0000
2015-01-01T13:00:00Z,2015-01-01T14:00:00+0100,46752.0000,37248.0000,2279.0000,0.0612,27913.0000,11921.0000,0.4271,525.0000,11396.0000
2015-01-01T14:00:00Z,2015-01-01T15:00:00+0100,47403.0000,37248.0000,746.0000,0.0200,27913.0000,11851.0000,0.4246,524.0000,11327.0000
2015-01-01T15:00:00Z,2015-01-01T16:00:00+0100,49440.0000,37248.0000,50.0000,0.0013,27913.0000,13582.0000,0.4866,524.0000,13058.0000
2015-01-01T16:00:00Z,2015-01-01T17:00:00+0100,53410.0000,37248.0000,0.0000,0.0000,27913.0000,15436.0000,0.5530,524.0000,14911.0000
2015-01-01T17:00:00Z,2015-01-01T18:00:00+0100,53672.0000,37248.0000,0.0000,0.0000,27913.0000,16868.0000,0.6043,524.0000,16344.0000
2015-01-01T18:00:00Z,2015-01-01T19:00:00+0100,53012.0000,37248.0000,0.0000,0.0000,27913.0000,18008.0000,0.6451,524.0000,17485.0000
2015-01-01T19:00:00Z,2015-01-01T20:00:00+0100,50313.0000,37248.0000,0.0000,0.0000,27913.0000,19181.0000,0.6872,522.0000,18659.0000
2015-01-01T20:00:00Z,2015-01-01T21:00:00+0100,48730.0000,37248.0000,0.0000,0.0000,27913.0000,20353.0000,0.7292,521.0000,19831.0000
2015-01-01T21:00:00Z,2015-01-01T22:00:00+0100,48624.0000,37248.0000,0.0000,0.0000,27913.0000,21235.0000,0.7608,519.0000,20716.0000
2015-01-01T22:00:00Z,2015-01-01T23:00:00+0100,45668.0000,37248.0000,0.0000,0.0000,27913.0000,22083.0000,0.7912,494.0000,21589.0000
2015-01-01T23:00:00Z,2015-01-02T00:00:00+0100,42424.0000,37250.0000,0.0000,0.0000,27926.0000,22472.0000,0.8047,305.0000,22167.0000
""",
    "open_power_system_data/generation_capacity/germany_2015_net_capacity.csv": """technology,capacity_mw,capacity_definition,source,source_type,year,country
Biomass and biogas,6532.0,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Fossil fuels,78400.0,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Hard coal,27000.0,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Hydro,10230.0,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Lignite,20800.0,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Natural gas,26700.0,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Nuclear,10800.0,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Offshore,4159.0,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Oil,3900.0,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Onshore,40299.58333333333,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Pumped storage,5666.0,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Solar,39321.83333333333,Net capacity,ENTSO-E SOAF,Other association,2015,DE
Wind,44458.58333333333,Net capacity,ENTSO-E SOAF,Other association,2015,DE
""",
    "fraunhofer_energy_charts/loom.md": """source: https://www.ise.fraunhofer.de/en/press-media/press-releases/2025/public-electricity-generation-2024-renewable-energies-cover-more-than-60-percent-of-german-electricity-consumption-for-the-first-time.html

# Fraunhofer Energy-Charts Notes

This table records selected values from Fraunhofer ISE's Energy-Charts analysis
of German net public electricity generation in 2024.

Human annotation:

These values provide recent context for German electricity modeling questions:
renewable share, wind and solar generation, grid load, battery capacity, and
pumped-storage capacity. They are not a model scenario and should not be mixed
with the 2015 OPSD files unless the modeling task explicitly chooses to do so.
""",
    "fraunhofer_energy_charts/germany_2024_public_power_context.csv": """metric,year,value,unit,source_note
renewable_share_net_public_generation,2024,62.7,percent,Fraunhofer ISE Energy-Charts analysis
wind_generation_net_public,2024,136.4,TWh,Fraunhofer ISE Energy-Charts analysis
onshore_wind_generation_net_public,2024,110.7,TWh,Fraunhofer ISE Energy-Charts analysis
offshore_wind_generation_net_public,2024,25.7,TWh,Fraunhofer ISE Energy-Charts analysis
solar_generation_total,2024,72.2,TWh,Fraunhofer ISE Energy-Charts analysis
hydropower_generation_net_public,2024,21.7,TWh,Fraunhofer ISE Energy-Charts analysis
biomass_generation_net_public,2024,36.0,TWh,Fraunhofer ISE Energy-Charts analysis
grid_load,2024,462.0,TWh,Fraunhofer ISE Energy-Charts analysis
battery_power_capacity,2024,12.1,GW,Fraunhofer ISE Energy-Charts analysis
battery_energy_capacity,2024,17.7,GWh,Fraunhofer ISE Energy-Charts analysis
pumped_storage_power_capacity,2024,10.0,GW,Fraunhofer ISE Energy-Charts analysis
""",
    "german_climate_policy/loom.md": """source: https://www.bundesregierung.de/breg-de/schwerpunkte/klimaschutz/climate-change-act-2021-1913970

# German Climate Policy Notes

This directory stores selected target values from the German Federal
Government's description of the 2021 Climate Change Act amendment.

Human annotation:

These are policy targets, not model constraints. A modeling agent may decide to
use them as scenario labels, validation context, or constraints, but that choice
belongs to the modeling workflow outside `raw_example`.
""",
    "german_climate_policy/climate_change_act_targets_2021.csv": """source,policy_name,target_year,metric,value_percent,value_bool
https://www.bundesregierung.de/breg-de/schwerpunkte/klimaschutz/climate-change-act-2021-1913970,German Climate Change Act 2021 amendment,2030,greenhouse_gas_reduction_vs_1990,65,
https://www.bundesregierung.de/breg-de/schwerpunkte/klimaschutz/climate-change-act-2021-1913970,German Climate Change Act 2021 amendment,2040,greenhouse_gas_reduction_vs_1990,88,
https://www.bundesregierung.de/breg-de/schwerpunkte/klimaschutz/climate-change-act-2021-1913970,German Climate Change Act 2021 amendment,2045,greenhouse_gas_neutrality,,true
https://www.bundesregierung.de/breg-de/schwerpunkte/klimaschutz/climate-change-act-2021-1913970,German Climate Change Act 2021 amendment,2050,negative_emissions_balance_goal,,true
""",
}
