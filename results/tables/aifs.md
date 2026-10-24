Evaluation sample: 01 Sep 2025 to 30 Sep 2026, 9,473 hours. Every input uses the same models (ensemble of linear, gradient boosting and neural network), monthly refits on the previous 180 days and the 30-day drift correction.


### onshore (MW; mean capacity 68,795 MW)

|                            |   MAE |   RMSE |   bias |   nMAE_% |   skill_vs_TSO_% |
|:---------------------------|------:|-------:|-------:|---------:|-----------------:|
| TSO day-ahead forecast     |  1267 |   1814 |     70 |     1.84 |              0   |
| ICON                       |  1741 |   2459 |     -2 |     2.53 |            -37.4 |
| ECMWF IFS                  |  1733 |   2438 |     20 |     2.52 |            -36.8 |
| ECMWF AIFS                 |  1937 |   2677 |     34 |     2.82 |            -53   |
| ECMWF IFS, 6-hourly        |  1950 |   2676 |     25 |     2.84 |            -53.9 |
| mean of IFS and ICON       |  1550 |   2199 |      9 |     2.25 |            -22.4 |
| mean of AIFS and ICON      |  1589 |   2251 |     16 |     2.31 |            -25.5 |
| mean of AIFS and IFS       |  1642 |   2318 |     27 |     2.39 |            -29.6 |
| mean of AIFS, IFS and ICON |  1513 |   2159 |     17 |     2.2  |            -19.5 |

Diebold-Mariano (daily mean absolute error; negative = first more accurate)

|                                                    |   MAE change % |   DM stat |   p-value |
|:---------------------------------------------------|---------------:|----------:|----------:|
| ECMWF AIFS vs ECMWF IFS                            |         11.789 |     4.091 |     0     |
| ECMWF AIFS vs ECMWF IFS, 6-hourly                  |         -0.642 |    -0.252 |     0.801 |
| ECMWF AIFS vs ICON                                 |         11.281 |     4.302 |     0     |
| mean of AIFS and ICON vs mean of IFS and ICON      |          2.534 |     1.449 |     0.147 |
| mean of AIFS, IFS and ICON vs mean of IFS and ICON |         -2.36  |    -1.981 |     0.048 |

### offshore (MW; mean capacity 10,154 MW)

|                            |   MAE |   RMSE |   bias |   nMAE_% |   skill_vs_TSO_% |
|:---------------------------|------:|-------:|-------:|---------:|-----------------:|
| TSO day-ahead forecast     |   552 |    777 |   -131 |     5.45 |              0   |
| ICON                       |   757 |   1018 |     28 |     7.48 |            -37   |
| ECMWF IFS                  |   704 |    957 |     26 |     6.95 |            -27.5 |
| ECMWF AIFS                 |   680 |    924 |     34 |     6.72 |            -23.2 |
| ECMWF IFS, 6-hourly        |   718 |    974 |     17 |     7.09 |            -30   |
| mean of IFS and ICON       |   681 |    924 |     27 |     6.72 |            -23.3 |
| mean of AIFS and ICON      |   664 |    905 |     31 |     6.56 |            -20.3 |
| mean of AIFS and IFS       |   654 |    892 |     30 |     6.46 |            -18.4 |
| mean of AIFS, IFS and ICON |   649 |    886 |     29 |     6.41 |            -17.6 |

Diebold-Mariano (daily mean absolute error; negative = first more accurate)

|                                                    |   MAE change % |   DM stat |   p-value |
|:---------------------------------------------------|---------------:|----------:|----------:|
| ECMWF AIFS vs ECMWF IFS                            |         -3.353 |    -1.732 |     0.083 |
| ECMWF AIFS vs ECMWF IFS, 6-hourly                  |         -5.251 |    -2.561 |     0.01  |
| ECMWF AIFS vs ICON                                 |        -10.112 |    -4.774 |     0     |
| mean of AIFS and ICON vs mean of IFS and ICON      |         -2.512 |    -2.586 |     0.01  |
| mean of AIFS, IFS and ICON vs mean of IFS and ICON |         -4.677 |    -7.699 |     0     |

### solar (MW; mean capacity 110,711 MW)

|                            |   MAE |   RMSE |   bias |   nMAE_% |   skill_vs_TSO_% |
|:---------------------------|------:|-------:|-------:|---------:|-----------------:|
| TSO day-ahead forecast     |   679 |   1340 |    -21 |     0.61 |              0   |
| ICON                       |   966 |   1858 |    -72 |     0.87 |            -42.2 |
| ECMWF IFS                  |  1030 |   1988 |    -62 |     0.92 |            -51.7 |
| ECMWF AIFS                 |  1108 |   2183 |    -89 |     0.99 |            -63.2 |
| mean of IFS and ICON       |   854 |   1614 |    -67 |     0.77 |            -25.7 |
| mean of AIFS and ICON      |   902 |   1736 |    -81 |     0.81 |            -32.7 |
| mean of AIFS and IFS       |   959 |   1838 |    -76 |     0.86 |            -41.1 |
| mean of AIFS, IFS and ICON |   857 |   1627 |    -74 |     0.77 |            -26.1 |

Diebold-Mariano (daily mean absolute error; negative = first more accurate)

|                                                    |   MAE change % |   DM stat |   p-value |
|:---------------------------------------------------|---------------:|----------:|----------:|
| ECMWF AIFS vs ECMWF IFS                            |          7.584 |     1.673 |     0.094 |
| ECMWF AIFS vs ICON                                 |         14.738 |     2.978 |     0.003 |
| mean of AIFS and ICON vs mean of IFS and ICON      |          5.588 |     1.867 |     0.062 |
| mean of AIFS, IFS and ICON vs mean of IFS and ICON |          0.32  |     0.189 |     0.85  |

### Correlation of hourly forecast errors

|          |   AIFS-IFS |   AIFS-ICON |   IFS-ICON |   AIFS-TSO |   IFS-TSO |
|:---------|-----------:|------------:|-----------:|-----------:|----------:|
| onshore  |       0.64 |        0.54 |       0.61 |       0.49 |      0.61 |
| offshore |       0.8  |        0.74 |       0.75 |       0.62 |      0.66 |
| solar    |       0.55 |        0.47 |       0.41 |       0.34 |      0.45 |

### Solar MAE by hour of day (UTC), MW, daylight hours

|   ts_utc |   TSO |   ICON |   ECMWF IFS |   ECMWF AIFS |
|---------:|------:|-------:|------------:|-------------:|
|        5 |   275 |    556 |         624 |          710 |
|        6 |   667 |   1002 |        1023 |         1173 |
|        7 |  1127 |   1550 |        1577 |         1723 |
|        8 |  1508 |   2078 |        2208 |         2321 |
|        9 |  1750 |   2441 |        2734 |         2803 |
|       10 |  1887 |   2625 |        2902 |         2996 |
|       11 |  1993 |   2669 |        2832 |         3051 |
|       12 |  1950 |   2617 |        2754 |         3004 |
|       13 |  1739 |   2310 |        2601 |         2722 |
|       14 |  1414 |   1757 |        1993 |         2188 |
|       15 |  1000 |   1256 |        1279 |         1445 |
|       16 |   516 |    856 |         811 |          922 |
|       17 |   172 |    478 |         486 |          633 |
|       18 |    63 |    196 |         233 |          296 |

### Imbalance cost at reBAP, EUR per MWh generated (9,473 hours)

|          |   TSO |   ICON |   ECMWF IFS |   ECMWF AIFS |   mean of IFS and ICON |   mean of AIFS, IFS and ICON |
|:---------|------:|-------:|------------:|-------------:|-----------------------:|-----------------------------:|
| onshore  |  1    |   0.63 |        1.2  |         1.07 |                   0.92 |                         0.97 |
| offshore |  0.66 |   1.57 |        1.02 |         0.69 |                   1.29 |                         1.09 |
| solar    |  1.92 |   1.53 |        1.85 |         1.61 |                   1.69 |                         1.67 |
