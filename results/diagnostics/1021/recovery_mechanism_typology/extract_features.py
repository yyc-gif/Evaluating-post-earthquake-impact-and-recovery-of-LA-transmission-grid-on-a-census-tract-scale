"""Linear post-processing of archived gated states; no physical model execution."""
from support import *
import geopandas as gpd
from scipy import sparse
from threadpoolctl import threadpool_limits

EDGES = np.array([0., 6., 24., 72., 168., 480.])


def widths(t, left, right):
    return np.maximum(0., np.minimum(t[1:], right)-np.maximum(t[:-1], left))


def main():
    protocol = git("log", "-1", "--format=%H", "--", str(HERE/"PROTOCOL.md")).decode().strip()
    git("merge-base", "--is-ancestor", protocol, "refs/remotes/origin/1021")
    a, f, refs, d = inputs()
    order = csv_payload("Data/Tracts_Within_Expanded_Area.csv", dtype={"GEOID":str})
    mapping = csv_payload("Data/JULY_UTILITY_CONSTRAINED_92.csv", dtype={"tract_id":str,"substation_id":str})
    integrals = np.load(ARCHIVE/FORMAL/"Formal_Offline_Evaluation/2pc50__C57_D1__impact-first__INTEGRALS.npz")
    stations = pd.Index(integrals["station_ids"].astype(str))
    ix = pd.Index(order.GEOID).get_indexer(f.tract_id)
    assert (ix >= 0).all()
    np.testing.assert_array_equal(order.population.to_numpy()[ix], f.Population)
    w = sparse.csr_matrix((mapping.weight, (pd.Index(order.GEOID).get_indexer(mapping.tract_id),
                                           stations.get_indexer(mapping.substation_id))), shape=(2315,92))
    mass = np.asarray(w.sum(1)).ravel()
    np.testing.assert_allclose(mass,1,atol=1e-12)
    w = sparse.diags(1/mass[ix]) @ w[ix]
    station_intervals = np.zeros((92,5))
    times, increments, qa = [], [], []
    events = pd.read_csv(PRIOR/"EVENT_SOURCE_HASHES_AND_IDENTITIES.csv")
    events = events[events.case == "2pc50__C57_D1__impact-first"].sort_values("realization_id")
    assert len(events) == 1000
    for m, row in enumerate(events.itertuples()):
        path = Path(row.event_path)
        assert sha(path) == row.event_npz_sha256
        assert sha(path.with_suffix(".json")) == row.event_manifest_sha256
        z = np.load(path, allow_pickle=False)
        t, e = z["event_time_hr"], z["e"]
        np.testing.assert_array_equal(z["station_ids"].astype(str),stations)
        assert t[0] == 0 and t[-1] == 480 and (np.diff(t)>0).all()
        interval = np.column_stack([(e[:-1]*widths(t,l,r)[:,None]).sum(0) for l,r in zip(EDGES[:-1],EDGES[1:])])
        loss = 480-interval.sum(1)
        err = np.max(abs(loss-integrals["G1_BASELINE_050__L_total"][m]))
        assert err < 1e-10
        station_intervals += interval/1000
        times.append(t)
        increments.append(np.vstack([e[0],np.diff(e,axis=0)])/1000)
        qa.append({"realization_id":row.realization_id,"max_station_integral_error":float(err),
                   "npz_sha256":row.event_npz_sha256,"physical_hash":row.physical_hash,
                   "DS_hash":row.DS_hash,"duration_hash":row.duration_hash})
    union, reverse = np.unique(np.concatenate(times),return_inverse=True)
    steps = np.zeros((len(union),92))
    np.add.at(steps,reverse,np.concatenate(increments))
    steps = np.cumsum(steps,axis=0)
    raw_a = w @ station_intervals / np.diff(EDGES)[None,:]
    b = (1-raw_a) @ np.diff(EDGES)
    initial = w @ steps[0]
    np.testing.assert_allclose(b,d.impact__B480_mean,atol=1e-10,rtol=0)
    np.testing.assert_allclose(initial,f.Init_Supply,atol=1e-12,rtol=0)
    # An independent route integrates the merged mean step history before mapping.
    from_steps = np.column_stack([(steps[:-1]*widths(union,l,r)[:,None]).sum(0)
                                  for l,r in zip(EDGES[:-1],EDGES[1:])])
    np.testing.assert_allclose(from_steps,station_intervals,atol=1e-9,rtol=0)
    raw_b = np.column_stack([initial, f.B_Unconstrained,
                            d.impact__B480_mean-d.unconstrained__B480_mean])
    assert np.isfinite(raw_a).all() and np.isfinite(raw_b).all()
    assert raw_a.min() >= -1e-12 and raw_a.max() <= 1+1e-12
    columns = ["availability_0_6","availability_6_24","availability_24_72",
               "availability_72_168","availability_168_480"]
    out = f[["tract_id","Population","SOVI_SCORE","frozen_SOVI_quartile",
             "additional_zero_housing_positive_population"]].copy()
    out[columns] = raw_a
    out[["initial_availability","baseline_deficit_hr","impact_increment_hr"]] = raw_b
    save("RECOVERY_FEATURES.csv",out)
    np.savez_compressed(HERE/"RECOVERY_MATRICES.npz",tract_ids=a["tract_ids"],A=raw_a,B=raw_b,
                        A_names=np.array(columns),B_names=np.array(["initial_availability","baseline_deficit_hr","impact_increment_hr"]),
                        edges=EDGES,station_ids=stations.to_numpy(dtype="U"),weights=w.toarray(),
                        mean_event_times=union,mean_station_availability=steps)
    save("EVENT_INTEGRAL_QA.csv",qa)
    geometry = gpd.read_file(AUTH/"study_domain_geometry.gpkg").set_index("tract_id").loc[f.tract_id]
    assert len(geometry) == 2299 and not geometry.geometry.is_empty.any() and geometry.crs.to_epsg() == 3310
    xy = np.column_stack([geometry.geometry.centroid.x,geometry.geometry.centroid.y])
    cells = np.floor(xy/20000).astype(int)
    hospital_path = "docs/data_research/stage7_path_b_p2_integration_review_20261014/FROZEN_P2_TRACT_TABLE_2315.csv"
    table = csv_payload(hospital_path,dtype={"tract_id":str}).set_index("tract_id").loc[f.tract_id]
    context = out[["tract_id","Population","SOVI_SCORE","frozen_SOVI_quartile",
                   "additional_zero_housing_positive_population"]].copy()
    context["hospital_tract"] = table.hospital_tract.to_numpy()
    context["x_m"], context["y_m"] = xy.T
    context["spatial_block"] = [f"{x}_{y}" for x,y in cells]
    save("CONTEXT_AND_SPATIAL_BLOCKS.csv",context)
    dump("FEATURE_EXTRACTION_QA.json",{
        "status":"PASS","protocol_commit":protocol,"protocol_sha256":sha(HERE/"PROTOCOL.md"),
        "source_events":1000,"eligible_tracts":2299,"population":int(f.Population.sum()),
        "zero_housing_included":int(f.additional_zero_housing_positive_population.sum()),
        "mean_curve_event_times":len(union),"occupied_spatial_blocks":len(np.unique(context.spatial_block)),
        "exact_total_integral_max_error":float(np.max(abs(b-d.impact__B480_mean))),
        "initial_availability_max_error":float(np.max(abs(initial-f.Init_Supply))),
        "merged_step_integral_max_error":float(np.max(abs(from_steps-station_intervals))),
        "hospital_source":hospital_path,"hospital_source_sha256":legacy.hashlib.sha256(payload(hospital_path)).hexdigest(),
        "no_interpolation_or_physical_recalculation":True,
        "A_variance":raw_a.var(0).tolist(),"B_variance":raw_b.var(0).tolist()})
    print((HERE/"FEATURE_EXTRACTION_QA.json").read_text())


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
