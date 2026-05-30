source: https://data.open-power-system-data.org/time_series/2020-10-06/
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
