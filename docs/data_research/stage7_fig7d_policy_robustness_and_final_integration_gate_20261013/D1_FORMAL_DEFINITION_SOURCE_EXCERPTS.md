> AUTHOR REVIEW - NOT FORMAL STAGE 7

5593:     # Historical hotspot output name is kept for plot-reader compatibility;
5594:     # its value is the FEMA NRI v1.19 SOVI_SCORE, not CDC 2022 RPL_THEMES.
5595:     df_main["Hotspot_SVI_Score"] = df_main["SOVI_SCORE"]
5596:
5597:     def _rank_pct_component(source_col: str, out_col: str) -> bool:
5605:
5606:     hotspot_component_defs = [
5607:         ("T80", "Hotspot_T80_RankPct"),
5608:         ("Pre_1970_Ratio", "Hotspot_Pre1970_RankPct"),
5609:         ("NRI_RISK_SCORE", "Hotspot_NRI_Risk_RankPct"),
5610:         ("Hotspot_SVI_Score", "Hotspot_SVI_RankPct"),
5611:     ]
5612:     hotspot_rank_cols = []
5616:
5617:     if hotspot_rank_cols:
5618:         df_main["SlowVulnerable_Hotspot_Score"] = df_main[hotspot_rank_cols].sum(axis=1)
5619:         df_main["SlowVulnerable_Hotspot_Rank"] = (
5620:             df_main["SlowVulnerable_Hotspot_Score"]
5621:             .rank(method="first", ascending=False)
5622:             .astype(int)
5624:     else:
5625:         logger.warning("Stage 7 hotspot score: no usable component columns found.")
5626:         df_main["SlowVulnerable_Hotspot_Score"] = 0.0
5627:         df_main["SlowVulnerable_Hotspot_Rank"] = np.arange(1, len(df_main) + 1)
5628:
5629:     hotspot_top_n = int(getattr(cfg, "STAGE7_HOTSPOT_TOP_N", 10))
5630:     df_main["SlowVulnerable_Hotspot_Top10"] = (
5631:         df_main["SlowVulnerable_Hotspot_Rank"] <= hotspot_top_n
5632:     )
5633:
5934:     )
5935:
5936:     top10_mask = df_main["SlowVulnerable_Hotspot_Top10"].astype(bool)
5937:     top10_cluster_agreement = float(
5938:         np.mean(
6100:         "scenario",
6101:         "cluster",
6102:         "SlowVulnerable_Hotspot_Rank",
6103:         "SlowVulnerable_Hotspot_Score",
6104:         "T80",
6105:         "Pre_1970_Ratio",
6106:         "NRI_RISK_SCORE",
6107:         "Hotspot_SVI_Score",
6108:         "Hotspot_T80_RankPct",
6109:         "Hotspot_Pre1970_RankPct",
6110:         "Hotspot_NRI_Risk_RankPct",
6111:         "Hotspot_SVI_RankPct",
6112:         "T50",
6113:         "Init_Supply",
6115:     hotspot_detail_cols = [c for c in hotspot_detail_cols if c in df_main.columns]
6116:     (
6117:         df_main.sort_values("SlowVulnerable_Hotspot_Rank")
6118:         .head(hotspot_top_n)[hotspot_detail_cols]
6119:         .to_csv(out_dir / "stage7_top10_slow_vulnerable_tracts.csv", index=False)
6137:         "NRI_BUILDVALUE",
6138:         "NRI_RISK_SCORE",
6139:         "Hotspot_SVI_Score",
6140:         "Hotspot_T80_RankPct",
6141:         "Hotspot_Pre1970_RankPct",
6142:         "Hotspot_NRI_Risk_RankPct",
6143:         "Hotspot_SVI_RankPct",
6144:         "SlowVulnerable_Hotspot_Score",
6145:         "SlowVulnerable_Hotspot_Rank",
6146:         "SlowVulnerable_Hotspot_Top10",
6147:     ] + [f"PC{i+1}" for i in range(n_components)]
6148:
6152:     df_main.to_csv(out_dir / "clusters_labels_final.csv", index=False)
6153:     full_domain_stage7 = full_domain_stage7.merge(
6154:         df_main[["tract_id", "cluster", "SlowVulnerable_Hotspot_Score"]],
6155:         on="tract_id", how="left", validate="one_to_one",
6156:     )
