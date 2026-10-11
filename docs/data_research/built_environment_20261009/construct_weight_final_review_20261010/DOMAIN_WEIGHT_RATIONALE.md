# Domain-weight rationale

The scientific target is a joint electricity-service recovery/community-characteristics description. Five equal domain budgets are defensible as an explicit conceptual balance, not a discovered optimum. The inherited scheme assigns distance budget in proportions associated with the earlier coordinate counts and places substantially more emphasis on grid dependency. Neither budget is a causal-effect weight or a guarantee of equal observed class separation.

## Predeclared path

For lambda in{0,.25,.50,.75,1}, w(lambda)=(1-lambda)w_equal+lambda w_inherited. StandardScaler uses population variance; each standardized coordinate is multiplied by sqrt(w_domain/number of retained coordinates in that domain). D remains log1p building value plus published unadjusted ALR percentile. BE1 retains the whole physical budget and shares it over two coordinates; it is a deliberate redistribution. The parent audit's fixed-coordinate deletion control isolates that redistribution and is not replaced here.

|   lambda_value |   recovery_service |   grid |   physical |   social |   loss_exposure |
|---------------:|-------------------:|-------:|-----------:|---------:|----------------:|
|         0.0000 |             0.2000 | 0.2000 |     0.2000 |   0.2000 |          0.2000 |
|         0.2500 |             0.1955 | 0.2409 |     0.1955 |   0.1727 |          0.1955 |
|         0.5000 |             0.1909 | 0.2818 |     0.1909 |   0.1455 |          0.1909 |
|         0.7500 |             0.1864 | 0.3227 |     0.1864 |   0.1182 |          0.1864 |
|         1.0000 |             0.1818 | 0.3636 |     0.1818 |   0.0909 |          0.1818 |

The equal scheme increases SOVI from 1/11 to 0.2 (a 2.2-fold squared-distance budget), reduces grid from 4/11 to 0.2 (factor 0.55), and raises the other three budgets from 2/11 to 0.2 (factor 1.1). In BE0 the equal physical-coordinate budget is .2/3, not .2 each. In BE1 it is .2/2. These are the full changes, not only an increase in social emphasis.

## Observed consequences

| be   |   lambda_a |   lambda_b |   n_seeds |   ARI_median |   ARI_min |   ARI_max |   reassigned_median |   reassigned_min |   reassigned_max |   split_entropy_median |
|:-----|-----------:|-----------:|----------:|-------------:|----------:|----------:|--------------------:|-----------------:|-----------------:|-----------------------:|
| BE0  |     0.0000 |     0.2500 |        20 |       0.9612 |    0.9488 |    0.9722 |             30.0000 |               22 |               39 |                 0.0556 |
| BE0  |     0.2500 |     0.5000 |        20 |       0.9501 |    0.9421 |    0.9573 |             39.5000 |               34 |               45 |                 0.0681 |
| BE0  |     0.5000 |     0.7500 |        20 |       0.8765 |    0.8344 |    0.9466 |             98.0000 |               43 |              133 |                 0.1440 |
| BE0  |     0.7500 |     1.0000 |        20 |       0.2400 |    0.2319 |    0.4305 |           1043.5000 |              568 |             1082 |                 0.5151 |
| BE1  |     0.0000 |     0.2500 |        20 |       0.9645 |    0.9438 |    0.9681 |             27.5000 |               25 |               43 |                 0.0511 |
| BE1  |     0.2500 |     0.5000 |        20 |       0.9319 |    0.9093 |    0.9404 |             54.0000 |               48 |               71 |                 0.0876 |
| BE1  |     0.5000 |     0.7500 |        20 |       0.9270 |    0.9054 |    0.9345 |             57.5000 |               52 |               76 |                 0.0935 |
| BE1  |     0.7500 |     1.0000 |        20 |       0.4460 |    0.4374 |    0.4556 |            564.0000 |              546 |              572 |                 0.4753 |

The largest observed reorganization in both physical definitions occurs between the prescribed 0.75 and 1 settings. This does not locate a continuous change point: the interval was not sampled further. Equal weighting is justified by the intended conceptual balance, not the relatively favorable seed/spatial metrics atlambda 0. No apparent plateau identifies correct weights. All conditional four-class claims must name the weights; inherited fixed k=4 results cannot be validated by earlier selectedk = 5 evidence.
