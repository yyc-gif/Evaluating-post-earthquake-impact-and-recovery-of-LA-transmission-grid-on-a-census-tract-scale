# Official rank reconstruction
AUTHOR REVIEW - NOT FORMAL STAGE 7

`SPL_CBM = EPL_NEHD + EPL_BURN + EPL_SMOKE + EPL_CFLD + EPL_DRGT + EPL_HRCN + EPL_RFLD + EPL_SWND + EPL_TRND`.

`RPL_CBM` nationally ranks SPL_CBM; not a mean of three equally weighted domain ranks. Heat contributes1/9, Wildfire2/9 and Extreme Events6/9 of declared indicator-count weight before final national ranking. Domain ranks are separately national ranks of their own component sums. `RPL_EJI_CBM` nationally ranks the sum of RPL_EBM, RPL_HVM, RPL_SVM and RPL_CBM, so it is excluded from the intended RQ3 construct. RPL_EJI, RPL_SER and RPL_SVM are also not standalone climate ranks.

For 83,509 nationally valid records, nine-percentile sum error is 8.88e-16. Independent minimum-rank/(N-1) national reconstruction differs by at most 4.9997605e-05, within four-decimal export rounding. National Spearman agreement=0.999999994449. SQL versus Excel rounding and ties are acknowledged; not claimed byte-identical to unrounded CDC processing.

| component      | type      |   unique_values |   zero_count |     Pearson |   Spearman |   covariance_share_of_local_SPL_variance |   incremental_linear_R2_for_published_rank |
|:---------------|:----------|----------------:|-------------:|------------:|-----------:|-----------------------------------------:|-------------------------------------------:|
| NEHD           | indicator |              62 |            0 |   0.30418   |   0.62138  |                               0.12215    |                                 0.079597   |
| SMOKE          | indicator |              23 |            0 |   0.14754   |   0.066793 |                               0.01784    |                                 0.0062798  |
| BURN           | indicator |              48 |         2251 |   0.29663   |   0.19779  |                               0.085262   |                                 0.040153   |
| CFLD           | indicator |              17 |         2224 |   0.41762   |   0.30093  |                               0.081058   |                                 0.011213   |
| DRGT           | indicator |               7 |            0 |   0.0011343 |   0.032409 |                              -0.0001019  |                                 6.6212e-05 |
| RFLD           | indicator |               2 |         1860 |   0.91832   |   0.67607  |                               0.69248    |                                 0.60718    |
| HRCN           | indicator |               1 |         2299 | nan         | nan        |                               0          |                                 0          |
| SWND           | indicator |              68 |            0 |   0.0015584 |  -0.08639  |                               0.00083436 |                                 0.00047777 |
| TRND           | indicator |               2 |         2298 |   0.023629  |   0.021784 |                               0.00047811 |                                 0.00089021 |
| Heat           | domain    |              62 |            0 |   0.30418   |   0.62138  |                               0.12215    |                                 0.079597   |
| Wildfire       | domain    |              70 |            0 |   0.29838   |   0.071631 |                               0.1031     |                                 0.060389   |
| Extreme Events | domain    |             132 |            0 |   0.92621   |   0.36666  |                               0.77475    |                                 0.74906    |

Covariance shares sum to1 over indicators and separately over domains; they are decomposition of *local SPL score* variance including shared geographic covariance, not causal percentages of climate damage or nominal CDC weights. Riverine rank has only two values (0 and0.8605),439 positive-ranked and1,860 zero-ranked tracts. It accounts for69.248% of local score variance and Pearson0.918 with final rank. Heat contributes12.215%, wildfire combined10.310%, coastal8.106%; other indicators contribute almost no local variation. Heat Spearman0.621 remains important to ordering within the low-flood group. CBM is not literally single-component, but is not locally balanced across nine hazards.

Drought rank lies0.9467-0.9868 with only seven values. Strong wind is low/low-variance; hurricane is constant0; tornado rank is positive in only one tract, with13 other positive estimates assigned percentile0. Raw positive measurements can therefore have no effective variation in the index.

National leave-one-indicator/domain reranks are labeled researcher diagnostics, never CDC official alternatives. Omitting hurricane leaves top230 LA membership unchanged (local Spearman effectively1) while shifting national percentile calibration. Omitting riverine retains53.48% of top230, and omitting heat51.74%; both matter in different ways. Large absolute national-rank shifts after deleting a nearly constant local component do not establish local-information dominance.
