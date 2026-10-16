"""Independent data, vector-geometry, color-function and preservation checks."""
from common import *
from color_design import rgb_to_lab,srgb_to_linear,RGB_TO_XYZ
from prepare_sources import visible_map_paths
import fitz
import geopandas as gpd
from PIL import Image


def path_vertices(d):
    values=[]
    for item in d["items"]:
        if item[0] in ["l","c"]:values.extend(v for p in item[1:] for v in p)
        elif item[0]=="re":values.extend(item[1])
        else:raise ValueError(item[0])
    return np.array(values)


def main():
    f,status=inputs()
    before=json.loads(lp(HERE/"PRESERVATION_BEFORE.json").read_text())
    assert snapshot()==before
    protected=json.loads(lp(HERE/"PROTECTED_950_HASHES.json").read_text())
    assert len(protected)==950 and all(sha(ARCHIVE/p)==h for p,h in protected.items())
    sources=pd.read_csv(lp(HERE/"SOURCE_HASHES.csv"))
    assert all(sha(HERE/row.local_path)==row.sha256 for row in sources.itertuples())
    manifest=json.loads(lp(HERE/"inputs/ARTIFACT_HASHES.json").read_text())
    assert all(sha(ROOT/"results/stage7/2026-10-14"/name)==wanted for name,wanted in manifest.items())
    fit=np.load(lp(ROOT/"results/stage7/2026-10-14/preprocessing_and_labels.npz"))
    np.testing.assert_array_equal(fit["tract_ids"],f.tract_id)
    np.testing.assert_array_equal(fit["K3_labels"]+1,f.K3_class)
    assert f.K3_class.value_counts().sort_index().tolist()==[1235,428,636]
    hh=(f.frozen_SOVI_quartile=="Q4") & (f.MeanTotal5>=P75)
    reference=pd.read_csv(lp(HERE/"inputs/ORIGINAL_94_GEOIDS.csv"),dtype={"tract_id":str})
    assert set(f.tract_id[hh])==set(reference.tract_id)
    assert int(f.Population[hh].sum())==350799
    assert len(f)==2299 and len(status)==2315 and f.Population.sum()==9066522
    assert (status.Population==0).sum()==16 and f.additional_zero_housing_positive_population.sum()==8
    # Exact frozen values, not recomputed vulnerability or population ranks.
    table=pd.read_csv(io.BytesIO(source("results/stage7/2026-10-14/tract_features.csv")),dtype={"tract_id":str},float_precision="round_trip")
    pd.testing.assert_frame_equal(f,table)
    mapping=json.loads(np.load(lp(HERE/"inputs/SOURCE_D_VECTOR_PATHS.npz"))["payload"].tobytes())
    doc=fitz.open(lp(HERE/"FIGURE7_CONTINUOUS_REVIEW.pdf"))
    positive,na,joint,clip=visible_map_paths(doc[0])
    print("Visible output vector counts:",len(positive),len(na),len(joint),flush=True)
    assert [len(positive),len(na),len(joint)]==[2303,16,94]
    geometry=[]
    for kind,new in [("positive",positive),("NA",na),("high_high",joint)]:
        old=mapping[kind]
        for src,dst in zip(old,new):
            v1,v2=path_vertices(src),path_vertices(dst)
            assert v1.shape==v2.shape
            error=float(abs(v1-v2).max())
            assert error<1.2e-4,(kind,src["tract_id"],error)
            assert abs(src["width"]-dst["width"])<1e-6
            assert src.get("even_odd")==dst.get("even_odd")
            if src.get("color") is not None:
                np.testing.assert_allclose(src["color"],dst["color"],atol=1e-4,rtol=0)
            if kind=="NA":
                np.testing.assert_allclose(src["fill"],dst["fill"],atol=1e-4,rtol=0)
                np.testing.assert_allclose(dst["fill"],[1,1,1],atol=1e-4,rtol=0)
            geometry.append({"tract_id":src["tract_id"],"kind":kind,"vertex_max_error_pt":error,
                             "original_linewidth_pt":src["width"],"candidate_linewidth_pt":dst["width"]})
    save("INDEPENDENT_OUTPUT_VECTOR_QA.csv",geometry)
    assert {d["tract_id"] for d in mapping["positive"]}==set(f.tract_id)
    assert {d["tract_id"] for d in mapping["high_high"]}==set(f.tract_id[hh])
    assert {d["tract_id"] for d in mapping["NA"]}==set(status.tract_id[status.Population==0])
    colors=pd.read_csv(lp(HERE/"TRACT_DISPLAY_COLORS.csv"),dtype={"tract_id":str},float_precision="round_trip")
    pd.testing.assert_series_equal(colors.SOVI_SCORE,f.SOVI_SCORE)
    pd.testing.assert_series_equal(colors.MeanTotal5,f.MeanTotal5)
    spec=json.loads(lp(HERE/"COLOR_MAPPING_SPECIFICATION.json").read_text())
    R=f.MeanTotal5.to_numpy();u=(R-R.min())/(R.max()-R.min());v=f.SOVI_SCORE.to_numpy()/100
    np.testing.assert_array_equal(colors.burden_u,u)
    np.testing.assert_array_equal(colors.vulnerability_v,v)
    expected_colors={}
    for design,info in spec["designs"].items():
        # Independent matrix algebra from the written specification.
        factor=np.interp(u,np.linspace(0,1,257),info["common_chroma_factors_at_257_burden_knots"])
        ab=(np.array(info["ab_at_SOVI_0"])+(np.array(info["ab_at_SOVI_100"])-np.array(info["ab_at_SOVI_0"]))*v[:,None])*factor[:,None]
        L=91-49*u;fy=(L+16)/116
        labratio=np.column_stack([fy+ab[:,0]/500,fy,fy-ab[:,1]/200])
        white=np.array([.3127/.329,1,(1-.3127-.329)/.329])
        xyz=np.where(labratio>6/29,labratio**3,3*(6/29)**2*(labratio-4/29))*white
        linear=np.linalg.solve(RGB_TO_XYZ,xyz.T).T
        assert linear.min()>=0 and linear.max()<=1
        rgb=np.where(linear<=.0031308,12.92*linear,1.055*linear**(1/2.4)-.055)
        np.testing.assert_allclose(rgb,colors[[design+"_R",design+"_G",design+"_B"]],atol=3e-15,rtol=0)
        np.testing.assert_allclose(rgb_to_lab(rgb)[:,0],L,atol=1e-12,rtol=0)
        expected_colors[design]=rgb
    lookup=dict(zip(f.tract_id,expected_colors["blue_amber"]))
    for src,dst in zip(mapping["positive"],positive):
        np.testing.assert_allclose(dst["fill"],lookup[src["tract_id"]],atol=1e-4,rtol=0)
    pixels=pd.read_csv(lp(HERE/"ABC_PIXEL_PRESERVATION.csv"))
    assert len(pixels)==6 and pixels.A_B_C_changed_color_channels.eq(0).all()
    # Embedded PDF function samples are an interpolation approximation, not bins.
    errors=[]
    from color_design import color
    for xref in range(1,doc.xref_length()):
        if doc.xref_get_key(xref,"FunctionType")==('int','0'):
            size=doc.xref_get_key(xref,"Size")[1]
            if size.replace(" ","")!="[129129]":continue
            samples=np.frombuffer(doc.xref_stream(xref),dtype=">u2").reshape(129,129,3)/65535
            rng=np.random.default_rng(20261015);q=rng.uniform(0,1,(5000,2))
            at=q*128;left=np.floor(at).astype(int);weight=at-left
            x,y=left.T;wx,wy=weight.T
            estimated=((1-wx)*(1-wy))[:,None]*samples[y,x]+(wx*(1-wy))[:,None]*samples[y,x+1]+((1-wx)*wy)[:,None]*samples[y+1,x]+(wx*wy)[:,None]*samples[y+1,x+1]
            exact=color(q[:,0],q[:,1],"blue_amber",spec["designs"]["blue_amber"]["common_chroma_factors_at_257_burden_knots"])
            error=np.sqrt(((rgb_to_lab(estimated)-rgb_to_lab(exact))**2).sum(1))
            errors.append(float(error.max()))
    assert len(errors)==1 and max(errors)<.15
    pdfqa=[]
    for path in sorted(lp(HERE).glob("*.pdf")):
        pdf=fitz.open(path)
        for i,page in enumerate(pdf):
            spans=[s for b in page.get_text("dict")["blocks"] for line in b.get("lines",[]) for s in line["spans"] if s["text"].strip()]
            fonts=[row for row in page.get_fonts() if pdf.extract_font(row[0])[3]]
            missing=[row for row in page.get_fonts() if not pdf.extract_font(row[0])[3]]
            assert not missing
            assert not page.get_images()
            assert all(page.rect.contains(fitz.Rect(s["bbox"])) for s in spans)
            pdfqa.append({"file":Path(path).name,"page":i+1,"width_inches":page.rect.width/72,"height_inches":page.rect.height/72,
                          "min_font_pt":min(s["size"] for s in spans),"raster_images":0,"embedded_font_records":len(fonts),"text_inside_page":True})
    text=" ".join(doc[0].get_text().split())
    assert "High vulnerability & high recovery burden" in text
    assert "D. Recovery burden and social vulnerability" in text
    assert "SOVI quartile" not in text and "Q4 and deficit" not in text
    d_spans=[s for b in doc[0].get_text("dict")["blocks"] for line in b.get("lines",[]) for s in line["spans"]
             if fitz.Rect(D_RECT).contains(fitz.Rect(s["bbox"])) and s["text"].strip()]
    assert d_spans and min(s["size"] for s in d_spans)>=7.49
    save("PDF_PUBLICATION_QA.csv",pdfqa)
    g=gpd.read_file(lp(HERE/"inputs/study_domain_geometry.gpkg")).set_index("tract_id").loc[f.tract_id]
    affine=json.loads(lp(HERE/"DATA_AND_GEOMETRY_QA.json").read_text())["PDF_affine"]
    area=g.area.to_numpy()*affine[0]*(-affine[2])*(25.4/72)**2
    save("TRACT_NATIVE_DISPLAY_SUPPORT.csv",pd.DataFrame({"tract_id":f.tract_id,"area_mm2_at_publication_size":area,"high_high":hh,
                                                           "below_one_mm2":area<1,"below_quarter_mm2":area<.25}))
    dump("INDEPENDENT_QA.json",{"status":"PASS","eligible_tracts":2299,"population":9066522,"NA_tracts":16,
        "high_high_tracts":94,"high_high_population":350799,"P75_hours":P75,"K3_labels_unchanged":True,
        "full_vector_path_checks":len(geometry),"max_vector_vertex_error_pt":max(row["vertex_max_error_pt"] for row in geometry),
        "output_GEOID_geometry_order_verified":True,"continuous_colors_independently_reconstructed":True,
        "legend_interpolation_max_DeltaE76":max(errors),"native_tracts_below_one_mm2":int((area<1).sum()),
        "native_tracts_below_quarter_mm2":int((area<.25).sum()),"high_high_below_one_mm2":int(((area<1)&hh).sum()),
        "A_C_changed_pixels_at_150_300_600_dpi":0,"protected_scientific_files":950,
        "publication_and_1021_worktrees_and_indexes_unchanged":True,"no_models_or_scientific_outputs_modified":True})
    dump("PRESERVATION_AFTER.json",{"identical_to_before":snapshot()==before,"protected_950_unchanged":True,
                                    "original_Figure7_actual_sha256":sha(PUBLICATION/"results/figure_review/Main/Fig07.pdf"),
                                    "1021_HEAD":git("rev-parse","refs/heads/1021"),"publication_HEAD":git("rev-parse","refs/heads/2026-10-14")})
    print(lp(HERE/"INDEPENDENT_QA.json").read_text())


if __name__=="__main__":main()
