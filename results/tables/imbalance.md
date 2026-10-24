Sample: 01 Dec 2024 to 30 Sep 2026, 16,054 hours with day-ahead price and all four quarter-hourly reBAP values. Price-taker portfolio with the profile of the national fleet; forecast sold day-ahead, whole error settled at reBAP (no intraday trading).


### Prices (EUR/MWh)

|             |   count |   mean |   std |     min |    1% |   50% |   99% |    max |
|:------------|--------:|-------:|------:|--------:|------:|------:|------:|-------:|
| day-ahead   |   16054 |   97.7 |  61.1 |  -499   | -19.6 |  99.3 | 264   |  936.3 |
| reBAP short |   16054 |  101.6 | 135.2 | -4218.4 | -67.4 |  98.6 | 369.5 | 4708.4 |
| reBAP long  |   16054 |  101.6 | 135.2 | -4218.4 | -67.4 |  98.6 | 369.5 | 4708.4 |
| ID-AEP      |   16054 |  101.2 | 107.8 | -2809.2 | -26.5 |  98.8 | 331.2 | 3971.1 |

### Imbalance cost of the forecast error, EUR per MWh generated

Spreads are volume-weighted: day-ahead minus reBAP when long, reBAP minus day-ahead when short.

|                                        |   EUR/MWh |   long side |   short side |   long, % of output |   short, % of output |   spread when long |   spread when short |
|:---------------------------------------|----------:|------------:|-------------:|--------------------:|---------------------:|-------------------:|--------------------:|
| ('onshore', 'TSO day-ahead forecast')  |      1.55 |        0.72 |         0.83 |                4.83 |                 4.95 |              14.92 |               16.78 |
| ('onshore', 'ICON + ECMWF ensemble')   |      1.2  |        0.63 |         0.57 |                5.26 |                 5.55 |              11.97 |               10.24 |
| ('onshore', 'Combination with TSO')    |      1.46 |        0.68 |         0.78 |                4.36 |                 5.14 |              15.61 |               15.12 |
| ('offshore', 'TSO day-ahead forecast') |      1.07 |        0.25 |         0.82 |               10.32 |                 7.34 |               2.44 |               11.14 |
| ('offshore', 'ICON + ECMWF ensemble')  |      1.7  |        0.4  |         1.3  |                9.32 |                10.48 |               4.34 |               12.37 |
| ('offshore', 'Combination with TSO')   |      1.23 |        0.32 |         0.92 |                9.39 |                 7.99 |               3.37 |               11.49 |
| ('solar', 'TSO day-ahead forecast')    |      2.19 |        0.99 |         1.21 |                4.06 |                 3.15 |              24.31 |               38.26 |
| ('solar', 'ICON + ECMWF ensemble')     |      1.74 |        0.71 |         1.03 |                4.16 |                 3.78 |              17.08 |               27.22 |
| ('solar', 'Combination with TSO')      |      2.13 |        0.97 |         1.16 |                3.74 |                 3.09 |              25.86 |               37.64 |
| ('total', 'TSO day-ahead forecast')    |      1.74 |        0.81 |         0.93 |                3.85 |                 3.19 |              20.95 |               29.11 |
| ('total', 'ICON + ECMWF ensemble')     |      1.46 |        0.7  |         0.77 |                3.77 |                 3.91 |              18.47 |               19.69 |
| ('total', 'Combination with TSO')      |      1.68 |        0.77 |         0.92 |                3.39 |                 3.36 |              22.65 |               27.34 |

### Imbalance cost by year, EUR/MWh (2024 = December only)

|                                        |   2024 |   2025 |   2026 |
|:---------------------------------------|-------:|-------:|-------:|
| ('onshore', 'TSO day-ahead forecast')  |   3.42 |   1.74 |   0.96 |
| ('onshore', 'ICON + ECMWF ensemble')   |   3.05 |   1.56 |   0.37 |
| ('onshore', 'Combination with TSO')    |   3.56 |   1.67 |   0.79 |
| ('offshore', 'TSO day-ahead forecast') |   5.93 |   1.16 |   0.38 |
| ('offshore', 'ICON + ECMWF ensemble')  |  11.87 |   1.51 |   0.73 |
| ('offshore', 'Combination with TSO')   |   6.98 |   1.25 |   0.53 |
| ('solar', 'TSO day-ahead forecast')    |  14.4  |   2.85 |   1.39 |
| ('solar', 'ICON + ECMWF ensemble')     |  12.16 |   1.88 |   1.46 |
| ('solar', 'Combination with TSO')      |  13.16 |   2.7  |   1.43 |
| ('total', 'TSO day-ahead forecast')    |   4.44 |   2.06 |   1.08 |
| ('total', 'ICON + ECMWF ensemble')     |   4.86 |   1.67 |   0.89 |
| ('total', 'Combination with TSO')      |   4.62 |   1.99 |   1.04 |

### Saving against the TSO forecast, per MWh and for a 1 GW portfolio

|                                       |   saving vs TSO forecast, EUR/MWh |   HAC t |   capacity factor |   kEUR per GW and year |
|:--------------------------------------|----------------------------------:|--------:|------------------:|-----------------------:|
| ('onshore', 'ICON + ECMWF ensemble')  |                             0.354 |    1.97 |             0.186 |                    575 |
| ('onshore', 'Combination with TSO')   |                             0.094 |    1.41 |             0.186 |                    154 |
| ('offshore', 'ICON + ECMWF ensemble') |                            -0.631 |   -1.48 |             0.316 |                  -1748 |
| ('offshore', 'Combination with TSO')  |                            -0.165 |   -1.41 |             0.316 |                   -456 |
| ('solar', 'ICON + ECMWF ensemble')    |                             0.453 |    1.92 |             0.089 |                    354 |
| ('solar', 'Combination with TSO')     |                             0.062 |    0.72 |             0.089 |                     48 |

### Prices against the national forecast error (TSO forecast), EUR/MWh

| wind + solar actual - TSO forecast, GW   |   reBAP long - day-ahead |   ID-AEP - day-ahead |   hours |
|:-----------------------------------------|-------------------------:|---------------------:|--------:|
| (-inf, -4.0]                             |                     44   |                 41.8 |     731 |
| (-4.0, -2.0]                             |                     34   |                 28.7 |    1550 |
| (-2.0, -1.0]                             |                     33.6 |                 28.8 |    1856 |
| (-1.0, 0.0]                              |                      7.7 |                  4.9 |    3050 |
| (0.0, 1.0]                               |                     -1.9 |                 -2.1 |    3282 |
| (1.0, 2.0]                               |                    -11   |                 -8.7 |    2567 |
| (2.0, 4.0]                               |                    -20.7 |                -16.1 |    2354 |
| (4.0, inf]                               |                    -36.9 |                -31.6 |     664 |

### Combined forecast: error settled at reBAP or the same error closed at the intraday index ID-AEP (hypothetical: assumes the error is known before intraday trading), EUR/MWh

|          |   at reBAP |   at ID-AEP |
|:---------|-----------:|------------:|
| onshore  |       1.46 |        1.5  |
| offshore |       1.23 |        1.69 |
| solar    |       2.13 |        1.45 |
| total    |       1.68 |        1.5  |

### Cost split: covariance with the imbalance spread (reBAP - day-ahead) and bias, EUR/MWh

reBAP short and long are equal in all 16,054 hours, so the split is exact. A negative correlation means the portfolio tends to be long when reBAP is below day-ahead.

|                                        |   EUR/MWh |   covariance term |   bias term |   corr(spread, error) |
|:---------------------------------------|----------:|------------------:|------------:|----------------------:|
| ('onshore', 'TSO day-ahead forecast')  |     1.551 |             1.547 |       0.004 |                -0.095 |
| ('onshore', 'ICON + ECMWF ensemble')   |     1.198 |             1.187 |       0.011 |                -0.065 |
| ('onshore', 'Combination with TSO')    |     1.457 |             1.426 |       0.031 |                -0.09  |
| ('offshore', 'TSO day-ahead forecast') |     1.07  |             1.187 |      -0.117 |                -0.041 |
| ('offshore', 'ICON + ECMWF ensemble')  |     1.701 |             1.655 |       0.045 |                -0.052 |
| ('offshore', 'Combination with TSO')   |     1.235 |             1.29  |      -0.055 |                -0.045 |
| ('solar', 'TSO day-ahead forecast')    |     2.192 |             2.228 |      -0.036 |                -0.135 |
| ('solar', 'ICON + ECMWF ensemble')     |     1.739 |             1.754 |      -0.015 |                -0.097 |
| ('solar', 'Combination with TSO')      |     2.13  |             2.156 |      -0.026 |                -0.137 |
| ('total', 'TSO day-ahead forecast')    |     1.735 |             1.761 |      -0.026 |                -0.155 |
| ('total', 'ICON + ECMWF ensemble')     |     1.465 |             1.459 |       0.005 |                -0.115 |
| ('total', 'Combination with TSO')      |     1.685 |             1.686 |      -0.001 |                -0.153 |

### ICON + ECMWF ensemble against the TSO forecast: accuracy and imbalance cost

|          |   MAE TSO, MW |   MAE own, MW |   saving, EUR/MWh |   HAC t |   saving, spread clipped to [-135, 213] |   HAC t (clipped) |
|:---------|--------------:|--------------:|------------------:|--------:|----------------------------------------:|------------------:|
| onshore  |      1214.51  |      1342.28  |             0.354 |   1.973 |                                   0.167 |             1.933 |
| offshore |       541.415 |       607.101 |            -0.631 |  -1.476 |                                  -0.296 |            -1.8   |
| solar    |       682.169 |       751.123 |             0.453 |   1.921 |                                   0.319 |             2.039 |
| total    |      1756.25  |      1914.2   |             0.27  |   2.036 |                                   0.168 |             2.3   |
