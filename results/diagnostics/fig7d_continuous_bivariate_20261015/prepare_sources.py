"""Bind actual approved PDF paths to original GEOIDs; no scientific regeneration."""
from common import *
import fitz
import geopandas as gpd


def visible_map_paths(page):
    stack={};positive=[];na=[];joint=[];clip=None;pending_fill=None
    for d in page.get_cdrawings(extended=True):
        level=d.get("level",0)
        stack={l:r for l,r in stack.items() if l<level}
        if d["type"]=="clip":stack[level]=fitz.Rect(d["scissor"]);continue
        if d["type"]=="group":continue
        rect=fitz.Rect(d["rect"]);visible=fitz.Rect(page.rect)
        for boundary in stack.values():visible &=boundary
        intersects=not (rect&visible).is_empty
        # Preserve subpixel multipart slivers whose replayed float32 envelope
        # can have zero width/height; their vector commands still exist.
        degenerate_inside=not visible.is_empty and visible.contains(rect.tl) and visible.contains(rect.br)
        if not(intersects or degenerate_inside) or not(299<rect.x0 and rect.y0>431 and rect.x1<476 and rect.y1<569):continue
        # MuPDF may report a quadrilateral B paint as adjacent fill and stroke
        # records. Reunite those actual output records, not synthetic geometry.
        if d["type"]=="f":
            pending_fill=d
            continue
        if (d["type"]=="s" and pending_fill is not None
                and d["seqno"]==pending_fill["seqno"]+1
                and d["rect"]==pending_fill["rect"] and d["level"]==pending_fill["level"]):
            stroke=d
            d={**pending_fill,**{k:stroke[k] for k in
                 ["color","width","lineCap","lineJoin","closePath","dashes","stroke_opacity"]},"type":"fs"}
        pending_fill=None
        if d.get("fill") is not None and abs(d.get("width",0)-.1)<.001:positive.append(d);clip=tuple(visible)
        elif d.get("fill") is not None and abs(d.get("width",0)-.45)<.001:na.append(d)
        elif d.get("fill") is None and abs(d.get("width",0)-.62)<.001:joint.append(d)
    return positive,na,joint,clip


def parts(frame):
    return [(row.Index,p) for row in frame.itertuples() for p in
            (row.geometry.geoms if row.geometry.geom_type=="MultiPolygon" else [row.geometry])]


def main():
    assert git("symbolic-ref","HEAD")=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==BASE
    before=snapshot()
    assert before["publication"]["HEAD"]==BASE
    dump("PRESERVATION_BEFORE.json",before)
    registry=[]
    mapping={"results/figure_review/Main/Fig07.pdf":"inputs/FIGURE7_APPROVED.pdf",
             "results/stage7/2026-10-14/tract_features.csv":"inputs/tract_features.csv",
             "results/stage7/2026-10-14/stage7_full_domain_tract_status.csv":"inputs/full_domain_status.csv",
             "results/stage7/2026-10-14/study_domain_geometry.gpkg":"inputs/study_domain_geometry.gpkg",
             "results/stage7/2026-10-14/ARTIFACT_HASHES.json":"inputs/ARTIFACT_HASHES.json",
             "docs/data_research/stage7_path_b_p2_integration_review_20261014/VERIFIED_94_COOCCURRENCE_GEOIDS.csv":"inputs/ORIGINAL_94_GEOIDS.csv"}
    for rel,name in mapping.items():
        data=source(rel);write(name,data)
        registry.append({"source_commit":BASE,"source_path":rel,"local_path":name,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)})
    protected=json.loads(source("docs/reproducibility/author_suite_final_layout_20261012/PRESERVATION_BEFORE.json"))["protected_files"]
    assert len(protected)==950 and all(sha(ARCHIVE/p)==h for p,h in protected.items())
    dump("PROTECTED_950_HASHES.json",protected)
    f,status=inputs()
    assert len(f)==2299 and len(status)==2315 and status.Population.eq(0).sum()==16
    assert f.tract_id.is_unique and f.tract_id.str.fullmatch(r"\d{11}").all()
    assert f.Population.sum()==9066522 and f.additional_zero_housing_positive_population.sum()==8
    r=f.MeanTotal5.to_numpy()
    identity=float(abs(r-(f.B_Unconstrained+f.MeanDelta)).max())
    assert identity<1e-12 and abs(np.quantile(r,.75)-P75)<1e-12
    hh=f.frozen_SOVI_quartile.eq("Q4") & f.MeanTotal5.ge(P75)
    old=pd.read_csv(lp(HERE/"inputs/ORIGINAL_94_GEOIDS.csv"),dtype={"tract_id":str})
    assert set(f.loc[hh,"tract_id"])==set(old.tract_id)
    assert hh.sum()==94 and f.Population[hh].sum()==350799
    f["high_high"]=hh
    save("VERIFIED_TRACT_DISPLAY_VALUES.csv",f[["tract_id","Population","SOVI_SCORE","B_Unconstrained","MeanDelta","MeanTotal5","frozen_SOVI_quartile","high_high","K3_class"]])
    save("HIGH_HIGH_94_GEOIDS.csv",f.loc[hh,["tract_id","Population","MeanTotal5","SOVI_SCORE","frozen_SOVI_quartile"]])
    g=gpd.read_file(lp(HERE/"inputs/study_domain_geometry.gpkg")).set_index("tract_id")
    g=g.join(status.set_index("tract_id"))
    assert g.crs.to_epsg()==3310 and g.geometry.notna().all()
    pdf=fitz.open(lp(HERE/"inputs/FIGURE7_APPROVED.pdf"))
    positive,na,joint,clip=visible_map_paths(pdf[0])
    pg=parts(g[g.Population>0]);ng=parts(g[g.Population==0]);jg=parts(g.loc[g.index.isin(f.loc[hh,"tract_id"])])
    assert len(positive)==len(pg)==2303 and len(na)==len(ng)==16 and len(joint)==len(jg)==94
    geo=np.array([poly.bounds for _,poly in pg]);target=np.array([d["rect"] for d in positive])
    xx=np.column_stack([geo[:,[0,2]].ravel(),np.ones(2*len(pg))])
    yy=np.column_stack([geo[:,[3,1]].ravel(),np.ones(2*len(pg))])
    sx,tx=np.linalg.lstsq(xx,target[:,[0,2]].ravel(),rcond=None)[0]
    sy,ty=np.linalg.lstsq(yy,target[:,[1,3]].ravel(),rcond=None)[0]
    bound_errors=[];pathrows=[]
    for kind,draws,geoms in [("positive",positive,pg),("NA",na,ng),("high_high",joint,jg)]:
        for d,(geoid,poly) in zip(draws,geoms):
            xmin,ymin,xmax,ymax=poly.bounds
            expected=np.array([sx*xmin+tx,sy*ymax+ty,sx*xmax+tx,sy*ymin+ty])
            error=float(abs(expected-np.array(d["rect"])).max())
            # One archived outline already differs slightly from its filled GPKG
            # envelope. Preserve that original path; do not silently repair it.
            permitted=.091 if (kind,geoid)==("high_high","06037701801") else 1e-4
            assert error<permitted,(geoid,kind,error)
            bound_errors.append(error)
            d["tract_id"]=geoid;d["kind"]=kind
            pathrows.append({"tract_id":geoid,"kind":kind,"source_seqno":d["seqno"],"bbox_max_error_pt":error,
                             "path_sha256":hashlib.sha256(json.dumps(d["items"]).encode()).hexdigest()})
    assert {d["tract_id"] for d in joint}==set(f.loc[hh,"tract_id"])
    payload=json.dumps({"positive":positive,"NA":na,"high_high":joint,"map_clip":clip},separators=(",",":")).encode()
    p=lp(HERE/"inputs/SOURCE_D_VECTOR_PATHS.npz")
    np.savez_compressed(p,payload=np.frombuffer(payload,dtype=np.uint8))
    save("SOURCE_VECTOR_TO_GEOID_QA.csv",pathrows)
    save("SOURCE_HASHES.csv",registry)
    dump("DATA_AND_GEOMETRY_QA.json",{
        "status":"PASS","source_commit":BASE,"existing_Figure7_sha256":sha(HERE/"inputs/FIGURE7_APPROVED.pdf"),
        "eligible_tracts":2299,"study_tracts":2315,"NA_zero_population":16,"included_zero_housing":8,
        "population":9066522,"Q4_tracts":int(f.frozen_SOVI_quartile.eq("Q4").sum()),"high_burden_tracts":int((r>=P75).sum()),
        "high_high_tracts":94,"high_high_population":350799,"P75_hours":P75,"P75_recomputed":float(np.quantile(r,.75)),
        "total_deficit_identity_max_error_hr":identity,"burden_range_hr":[float(r.min()),float(r.max())],
        "SOVI_range":[float(f.SOVI_SCORE.min()),float(f.SOVI_SCORE.max())],
        "source_geography_EPSG":3310,"PDF_affine":[sx,tx,sy,ty],"map_clip_pt":clip,
        "all_source_path_geometry_reused":True,"max_geographic_bbox_error_pt":max(bound_errors),
        "archived_outline_envelope_exception":{"tract_id":"06037701801","maximum_difference_pt":max(bound_errors),
            "treatment":"Exact original PDF outline retained, not redrawn or silently corrected"},
        "positive_polygon_parts":2303,"NA_paths":16,"high_high_boundary_paths":94,
        "protected_scientific_files_unchanged":950,"no_quartiles_or_models_recalculated":True})
    debug=lp(HERE/"PDF_DRAWING_SAMPLE.json")
    if debug.is_file():debug.unlink()
    print((lp(HERE/"DATA_AND_GEOMETRY_QA.json")).read_text())


if __name__=="__main__":main()
