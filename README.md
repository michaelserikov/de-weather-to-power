# From weather forecasts to power: day-ahead wind and solar generation in Germany (v0.1)

[![tests](https://github.com/michaelserikov/de-weather-to-power/actions/workflows/tests.yml/badge.svg)](https://github.com/michaelserikov/de-weather-to-power/actions/workflows/tests.yml)

How well can German wind and solar generation for tomorrow be forecast from public weather forecasts, and does such a forecast add anything to the forecast the transmission system operators (TSOs) publish? This project turns day-ahead numerical weather predictions (DWD ICON and ECMWF IFS, issued about 24 hours before the valid hour) at 52 points into hourly forecasts of onshore wind, offshore wind and solar generation, evaluates them out of sample over 22 months (December 2024 to September 2026, 16,054 hours) and compares and combines them with the TSO day-ahead forecast.

**Main findings**
- A public-data model does not beat the TSOs on its own, but it carries independent information. Combining it with the TSO forecast (a linear combination re-estimated every month on past forecasts only) lowers the TSO's mean absolute error by 2.9% for onshore wind (Diebold-Mariano p = 0.001), 5.2% for solar (p = 0.005) and 1.5% for offshore wind (p = 0.09). The error of total wind and solar generation, which is what moves residual load and prices, falls from 1.76 to 1.68 GW.
- Two weather models are better than one. Adding ECMWF to ICON cuts the error of the stand-alone forecast by 15% for onshore wind, 10% for offshore wind and 8% for solar.
- The weather forecast is not where most of the error comes from. The same models fed with ERA5 reanalysis, i.e. with the weather that actually happened, still miss onshore wind by 1.22 GW, against 1.34 GW with the day-ahead forecasts. Most of the remaining error lies in translating coarse point weather into fleet output (where the turbines are, hub heights, outages, curtailment), so that is where the next gains are.
- The largest error of the period is not a weather error. On Easter Sunday, 5 April 2026, the day-ahead price fell to -105 EUR/MWh and onshore wind output dropped from about 34 GW to 10 GW around noon while every forecast stayed above 33 GW: plants were switched off at negative prices. Across all 1,041 negative-price hours, forecasts overestimate onshore wind by 1.5 GW (TSO) to 2.0 GW (this model). Giving the models the expected solar output and the day type (working day, Saturday, Sunday or holiday) lets them anticipate part of it: the onshore error in negative-price hours falls by 11% and the overall onshore error by 5%.
- Fed-in solar power per unit of irradiance and installed capacity fell by about 10% between summer 2024 and summer 2025, so a model trained on last year overestimates this year (bias +390 MW). This is consistent with rising self-consumption and with the rules for new systems in force since 25 February 2025 (no feed-in payment in negative-price hours, feed-in limited to 60% of rated power without a smart meter). A rolling correction of the forecast level over the last 30 days, with a two-day publication lag, removes the bias and lowers the solar error by 12%.

## Results

Mean absolute error in MW and in % of installed capacity (nMAE), 1 Dec 2024 to 30 Sep 2026, all forecasts out of sample. Skill is the reduction of MAE relative to the TSO forecast.

| | Onshore wind MAE | nMAE | skill | Offshore wind MAE | nMAE | skill | Solar MAE | nMAE | skill |
|---|---|---|---|---|---|---|---|---|---|
| TSO day-ahead forecast | 1,215 | 1.81% | | 541 | 5.56% | | 682 | 0.65% | |
| ICON, ensemble | 1,572 | 2.35% | -29% | 678 | 6.96% | -25% | 812 | 0.77% | -19% |
| ICON + ECMWF, ensemble | 1,342 | 2.00% | -10% | 607 | 6.24% | -12% | 751 | 0.71% | -10% |
| **Combination of ICON + ECMWF and TSO** | **1,179** | **1.76%** | **+2.9%** | **533** | **5.48%** | **+1.5%** | **646** | **0.62%** | **+5.2%** |
| ERA5 ensemble (weather known) | 1,221 | 1.82% | -0.6% | 560 | 5.74% | -3.3% | 851 | 0.81% | -25% |

Mean installed capacity over the sample: onshore 67.1 GW, offshore 9.8 GW, solar 105.0 GW. Full tables, including the single models and Diebold-Mariano tests: [results/tables/results.md](results/tables/results.md).

For solar, the ERA5 run is worse than the day-ahead forecasts: ERA5 (about 31 km) resolves clouds less well than ICON (down to 2 km over Germany), so reanalysis is a good stand-in for "known weather" for wind but not for solar irradiance.

![Monthly error](results/figures/fig1_monthly_nmae.png)

![Error by hour of day](results/figures/fig2_mae_by_hour.png)

The stand-alone model is weakest for onshore and offshore wind around midday, when curtailment at negative prices is most frequent, and for solar at the noon peak. In the evening (18:00-21:00 UTC), when onshore wind ramps matter most for the evening price peak, it is more accurate than the TSO forecast (1.33 vs 1.47 GW at 21:00 UTC), and this is where the combination gains most.

![Easter 2026](results/figures/fig4_worst_week_onshore.png)

The models learn where the capacity is. The point weights of the non-negative linear model put most offshore weight on the North Sea clusters, and most solar weight in the south, without being told where any plant stands:

![Learnt point weights](results/figures/fig3_point_weights.png)

## Method

**Data** (2024-02-20 to 2026-09-30, hourly, UTC)
- Weather: [Open-Meteo](https://open-meteo.com) at 46 onshore grid points (1 degree) and 6 offshore wind clusters. Day-ahead forecasts from the previous-runs API (`_previous_day1`: the run about 24 hours before the valid hour) for DWD ICON (`icon_seamless`) and ECMWF IFS 0.25 degree; ERA5 reanalysis from the archive API. Variables: wind at 10 m and 100 m, global and direct radiation, 2 m temperature.
- Generation, TSO day-ahead forecasts and day-ahead prices: [SMARD](https://www.smard.de) (Bundesnetzagentur), bidding zone DE-LU.
- Installed capacity, monthly: [Energy-Charts](https://energy-charts.info) (Fraunhofer ISE); solar as AC capacity.

**Alignment.** SMARD labels an hour by its start. Open-Meteo radiation is the mean over the preceding hour and wind is instantaneous, so radiation is shifted by one hour and wind is averaged over the two ends of each hour.

**Features.** Wind at hub height (135 m onshore, 110 m offshore) from the 100 m wind and the local shear exponent between 10 m and 100 m, passed through a generic power curve (cut-in 3 m/s, rated 11.5 m/s, cut-out 25 m/s); PV output from irradiance with a cell-temperature correction (-0.4% per kelvin); national means and spread; hour, season and day type; expected solar output in the wind models and expected wind output in the solar model.

**Models.** All models predict the national capacity factor (generation / installed capacity), so fleet growth does not have to be learnt.
- Non-negative linear regression on the per-point power-curve or PV features (one weight per point)
- Histogram gradient boosting and a feed-forward neural network (two hidden layers, 64 and 32 units) on per-point hub wind or irradiance plus the national and calendar features
- Ensemble: mean of the three; then a rolling level correction (ratio of actual to forecast energy over the previous 30 days, lagged by two days so that it uses only published data)
- Combination with the TSO forecast: linear regression of the actual on both forecasts, re-estimated monthly on all earlier out-of-sample forecasts

**Evaluation.** Rolling origin: at the start of each month all models are refitted on the previous 365 days and forecast the month ahead. MAE, RMSE, bias, nMAE; Diebold-Mariano test on daily mean absolute errors with a Newey-West variance (7 lags).

## Limitations
- Coarse weather points (1 degree grid) and no plant register (Marktstammdatenregister): the models infer where capacity stands from the data.
- The "actual" wind and solar generation published for Germany is partly based on TSO estimates (extrapolation from reference measurements), which may favour the TSO forecast in this comparison.
- The TSO forecast and the weather forecasts are not issued at exactly the same time; both are day-ahead, with leads of roughly one day.
- Curtailment is anticipated only through weather and calendar features, without a price forecast; the negative-price hours remain the largest source of error.
- Point forecasts only; no probabilistic forecasts, intraday updates or plant-level data.

## Run it

```bash
pip install -e ".[test]"
python scripts/download.py     # SMARD, Energy-Charts and Open-Meteo data, cached in data/raw (about 1 hour, API rate limits)
python -m wxpower.run          # rolling forecasts and evaluation (about 30 minutes), writes results/
pytest -q                      # 14 tests on synthetic data, no download needed
```

## Data licences
- Open-Meteo.com, CC BY 4.0 (ERA5: Copernicus Climate Change Service; ICON: Deutscher Wetterdienst; IFS: ECMWF)
- Bundesnetzagentur | SMARD.de, CC BY 4.0
- Energy-Charts, Fraunhofer ISE, CC BY 4.0
