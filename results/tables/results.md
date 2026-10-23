Evaluation sample: 01 Dec 2024 to 30 Sep 2026, 16,054 hours, all forecasts out of sample (monthly refits on earlier hours only).


### onshore (MW; mean capacity 67,088 MW)

|                                                 |   MAE |   RMSE |   bias |   nMAE_% |   skill_vs_TSO_% |
|:------------------------------------------------|------:|-------:|-------:|---------:|-----------------:|
| TSO day-ahead forecast                          |  1215 |   1725 |     14 |     1.81 |              0   |
| ICON, linear (point weights)                    |  1643 |   2363 |     35 |     2.45 |            -35.3 |
| ICON, gradient boosting                         |  1589 |   2208 |      2 |     2.37 |            -30.8 |
| ICON, neural network                            |  1942 |   2674 |     11 |     2.9  |            -59.9 |
| ICON, ensemble                                  |  1572 |   2207 |     14 |     2.35 |            -29.4 |
| ICON + ECMWF, ensemble without drift correction |  1325 |   1890 |     17 |     1.98 |             -9.1 |
| ICON + ECMWF, ensemble                          |  1342 |   1925 |     35 |     2    |            -10.5 |
| Meta (ICON + ECMWF ensemble and TSO)            |  1179 |   1671 |     97 |     1.76 |              2.9 |
| ERA5 ensemble (weather known)                   |  1221 |   1794 |     31 |     1.82 |             -0.6 |

Diebold-Mariano (daily mean absolute error; negative = more accurate than TSO)

|                                      |   DM stat vs TSO |   p-value |
|:-------------------------------------|-----------------:|----------:|
| ICON, ensemble                       |           10.77  |     0     |
| ICON + ECMWF, ensemble               |            5.255 |     0     |
| Meta (ICON + ECMWF ensemble and TSO) |           -3.327 |     0.001 |
| ERA5 ensemble (weather known)        |            0.253 |     0.8   |

### offshore (MW; mean capacity 9,770 MW)

|                                                 |   MAE |   RMSE |   bias |   nMAE_% |   skill_vs_TSO_% |
|:------------------------------------------------|------:|-------:|-------:|---------:|-----------------:|
| TSO day-ahead forecast                          |   541 |    767 |    -91 |     5.56 |              0   |
| ICON, linear (point weights)                    |   711 |    981 |     33 |     7.31 |            -31.3 |
| ICON, gradient boosting                         |   714 |    971 |     39 |     7.34 |            -31.9 |
| ICON, neural network                            |   794 |   1075 |     38 |     8.16 |            -46.7 |
| ICON, ensemble                                  |   678 |    919 |     35 |     6.96 |            -25.3 |
| ICON + ECMWF, ensemble without drift correction |   649 |    906 |      7 |     6.63 |            -19.9 |
| ICON + ECMWF, ensemble                          |   607 |    836 |     35 |     6.24 |            -12.1 |
| Meta (ICON + ECMWF ensemble and TSO)            |   533 |    749 |    -43 |     5.48 |              1.5 |
| ERA5 ensemble (weather known)                   |   560 |    777 |     36 |     5.74 |             -3.3 |

Diebold-Mariano (daily mean absolute error; negative = more accurate than TSO)

|                                      |   DM stat vs TSO |   p-value |
|:-------------------------------------|-----------------:|----------:|
| ICON, ensemble                       |           11.356 |     0     |
| ICON + ECMWF, ensemble               |            6.083 |     0     |
| Meta (ICON + ECMWF ensemble and TSO) |           -1.702 |     0.089 |
| ERA5 ensemble (weather known)        |            1.503 |     0.133 |

### solar (MW; mean capacity 105,005 MW)

|                                                 |   MAE |   RMSE |   bias |   nMAE_% |   skill_vs_TSO_% |
|:------------------------------------------------|------:|-------:|-------:|---------:|-----------------:|
| TSO day-ahead forecast                          |   682 |   1334 |    -86 |     0.65 |              0   |
| ICON, linear (point weights)                    |   991 |   1890 |    -62 |     0.94 |            -45.3 |
| ICON, gradient boosting                         |   805 |   1606 |    -22 |     0.77 |            -18   |
| ICON, neural network                            |   950 |   1865 |    -39 |     0.9  |            -39.2 |
| ICON, ensemble                                  |   812 |   1602 |    -43 |     0.77 |            -19   |
| ICON + ECMWF, ensemble without drift correction |   854 |   1634 |    389 |     0.82 |            -25.2 |
| ICON + ECMWF, ensemble                          |   751 |   1451 |    -36 |     0.71 |            -10.1 |
| Meta (ICON + ECMWF ensemble and TSO)            |   646 |   1266 |    -62 |     0.62 |              5.2 |
| ERA5 ensemble (weather known)                   |   851 |   1667 |    -54 |     0.81 |            -24.8 |

Diebold-Mariano (daily mean absolute error; negative = more accurate than TSO)

|                                      |   DM stat vs TSO |   p-value |
|:-------------------------------------|-----------------:|----------:|
| ICON, ensemble                       |            4.966 |     0     |
| ICON + ECMWF, ensemble               |            3.08  |     0.002 |
| Meta (ICON + ECMWF ensemble and TSO) |           -2.811 |     0.005 |
| ERA5 ensemble (weather known)        |            6.384 |     0     |

### Wind + solar total, MAE in GW by year

|                                      |   2024 |   2025 |   2026 |   all |
|:-------------------------------------|-------:|-------:|-------:|------:|
| TSO day-ahead forecast               |   1.81 |   1.7  |   1.83 |  1.76 |
| ICON, ensemble                       |   2.43 |   2.13 |   2.31 |  2.22 |
| ICON + ECMWF, ensemble               |   1.95 |   1.8  |   2.06 |  1.91 |
| Meta (ICON + ECMWF ensemble and TSO) |   1.72 |   1.63 |   1.75 |  1.68 |

### Negative-price hours (1041 of 16054 hours), MW

|                                                      |   MAE price<0 |   bias price<0 |   MAE price>=0 |
|:-----------------------------------------------------|--------------:|---------------:|---------------:|
| ('onshore', 'TSO day-ahead forecast')                |          2023 |           1484 |           1158 |
| ('onshore', 'ICON + ECMWF, ensemble')                |          2400 |           1961 |           1269 |
| ('onshore', 'Meta (ICON + ECMWF ensemble and TSO)')  |          2090 |           1713 |           1116 |
| ('offshore', 'TSO day-ahead forecast')               |           725 |            272 |            529 |
| ('offshore', 'ICON + ECMWF, ensemble')               |           925 |            618 |            585 |
| ('offshore', 'Meta (ICON + ECMWF ensemble and TSO)') |           745 |            399 |            518 |
| ('solar', 'TSO day-ahead forecast')                  |          1765 |            307 |            607 |
| ('solar', 'ICON + ECMWF, ensemble')                  |          1785 |            535 |            679 |
| ('solar', 'Meta (ICON + ECMWF ensemble and TSO)')    |          1644 |            576 |            577 |
