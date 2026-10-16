"""Vector-only D replacements; original A-C are imported, never regenerated."""
from common import *
from color_design import color,lab_to_linear,linear_to_srgb,simulate,DESIGNS,MACHADO,audit
import fitz
from PIL import Image,ImageDraw,ImageFont

W,H=518.4000244140625,648.
LEGEND=(326.,577.,487.,610.)
TITLE="D. Recovery burden and social vulnerability"
HH_LABEL="High vulnerability & high recovery burden"


def font(page):
    page.insert_font(fontname="ReviewBody",fontfile=str(FONT))
    page.insert_font(fontname="ReviewBold",fontfile=str(BOLD))


def text(page,xy,label,size=7.5,bold=False,align="left",rotate=0):
    name="ReviewBold" if bold else "ReviewBody"
    if align=="center":
        metrics=fitz.Font(fontfile=str(BOLD if bold else FONT))
        xy=(xy[0]-metrics.text_length(label,fontsize=size)/2,xy[1])
    page.insert_text(xy,label,fontname=name,fontsize=size,rotate=rotate,color=(.08,.08,.08))


def drawing_code(d,rgb=None):
    commands=[];last=None
    for item in d["items"]:
        op=item[0]
        if op=="l":
            a,b=item[1:]
            if last is None or tuple(a)!=tuple(last):commands.append(f"{a[0]:.8f} {a[1]:.8f} m")
            commands.append(f"{b[0]:.8f} {b[1]:.8f} l");last=b
        elif op=="c":
            a,b,c,e=item[1:]
            if last is None or tuple(a)!=tuple(last):commands.append(f"{a[0]:.8f} {a[1]:.8f} m")
            commands.append(" ".join(f"{v:.8f}" for p in [b,c,e] for v in p)+" c");last=e
        elif op=="re":
            x0,y0,x1,y1=item[1]
            points=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
            if len(item)>2 and item[2]<0:points=points[::-1]
            commands.append(f"{points[0][0]:.8f} {points[0][1]:.8f} m")
            commands.extend(f"{x:.8f} {y:.8f} l" for x,y in points[1:]);commands.append("h");last=None
        else:raise ValueError(op)
    if d.get("closePath"):commands.append("h")
    stroke=d.get("color");fill=rgb if rgb is not None else d.get("fill")
    setup=[f"{d.get('width',0):.8f} w",f"{int(d.get('lineJoin',0))} j",
           f"{int(d.get('lineCap',[0])[0])} J",d.get("dashes","[] 0")+" d"]
    if stroke is not None:setup.append(" ".join(f"{x:.10f}" for x in stroke)+" RG")
    if fill is not None:setup.append(" ".join(f"{x:.10f}" for x in fill)+" rg")
    operator=("B" if stroke is not None else "f") if fill is not None else "S"
    if d.get("even_odd") and fill is not None:operator+="*"
    return "q\n"+"\n".join(setup+commands+[operator,"Q"])+"\n"


def append_content(page,raw):
    doc=page.parent;xref=doc.get_new_xref();doc.update_object(xref,"<< >>");doc.update_stream(xref,raw.encode("ascii"))
    old=page.get_contents();doc.xref_set_key(page.xref,"Contents","["+" ".join(f"{x} 0 R" for x in [*old,xref])+"]")


def shade(page,rect,colors,label):
    """PDF Type1 function shading, not image or classified rectangular swatches."""
    doc=page.parent;n=colors.shape[0]
    fun=doc.get_new_xref()
    doc.update_object(fun,f"<< /FunctionType 0 /Domain [0 1 0 1] /Range [0 1 0 1 0 1] /Size [{n} {n}] /BitsPerSample 16 /Order 1 /Encode [0 {n-1} 0 {n-1}] /Decode [0 1 0 1 0 1] >>")
    doc.update_stream(fun,np.rint(colors*65535).astype(">u2").tobytes())
    shading=doc.get_new_xref()
    doc.update_object(shading,f"<< /ShadingType 1 /ColorSpace /DeviceRGB /Domain [0 1 0 1] /Function {fun} 0 R /AntiAlias true >>")
    resources=doc.xref_get_key(page.xref,"Resources")
    assert resources[0]=="xref"
    rid=int(resources[1].split()[0])
    doc.xref_set_key(rid,"Shading/"+label,f"{shading} 0 R")
    x0,y0,x1,y1=rect
    append_content(page,f"q {x1-x0:.8f} 0 0 {y1-y0:.8f} {x0:.8f} {page.rect.height-y1:.8f} cm /{label} sh Q")


def legends(page,spec,design,scalar=None):
    font(page);lo=spec["burden_normalization"]["minimum_hr"];hi=spec["burden_normalization"]["maximum_hr"]
    u,v=np.meshgrid(np.linspace(0,1,129),np.linspace(0,1,129))
    if scalar is None:
        scale=spec["designs"][design]["common_chroma_factors_at_257_burden_knots"]
        rgb=color(u,v,design,scale)
    else:
        lab=np.stack([91-49*u,np.zeros_like(u),np.zeros_like(u)],axis=-1)
        rgb=linear_to_srgb(lab_to_linear(lab))
    rect=LEGEND if scalar is None else (326.,590.,487.,602.)
    shade(page,rect,rgb,"ReviewGradient")
    x0,y0,x1,y1=rect
    page.draw_rect(fitz.Rect(rect),color=(.2,.2,.2),width=.35)
    ticks=[25,35,45,50] if scalar!="SOVI" else [0,25,50,75,100]
    limits=(lo,hi) if scalar!="SOVI" else (0.,100.)
    for value in ticks:
        px=x0+(value-limits[0])/(limits[1]-limits[0])*(x1-x0)
        page.draw_line((px,y1),(px,y1+2),color=(.2,.2,.2),width=.35)
        text(page,(px,y1+9),str(value),align="center")
    if scalar is None:
        for value in [0,50,100]:
            py=y1-value/100*(y1-y0)
            page.draw_line((x0-2,py),(x0,py),color=(.2,.2,.2),width=.35)
            metrics=fitz.Font(fontfile=str(FONT));width=metrics.text_length(str(value),fontsize=7.5)
            text(page,(x0-5-width,py+2.6),str(value))
        label="SOVI score (0-100)"
        length=fitz.Font(fontfile=str(FONT)).text_length(label,fontsize=7.5)
        text(page,(296.,(y0+y1+length)/2),label,rotate=90)
    text(page,((x0+x1)/2,y1+19),"Equivalent service-deficit hours" if scalar!="SOVI" else "SOVI score (0-100)",align="center")
    page.draw_rect(fitz.Rect(276.5,635.5,285.5,641.5),color=(.0666667,)*3,width=.62)
    text(page,(290.,642.5),HH_LABEL)
    page.draw_rect(fitz.Rect(466.,635.5,475.,641.5),color=(.2,.2,.2),fill=(1,1,1),width=.45)
    text(page,(479.,642.5),"N/A (16)")


def panel_canvas(spec,design,paths,f,scalar=None):
    doc=fitz.open();page=doc.new_page(width=W,height=H)
    lookup=f.set_index("tract_id")
    lo,hi=spec["burden_normalization"]["minimum_hr"],spec["burden_normalization"]["maximum_hr"]
    selected=[]
    for d in paths["positive"]:
        row=lookup.loc[d["tract_id"]]
        u=(row.MeanTotal5-lo)/(hi-lo)
        if scalar is None:
            rgb=color(np.array(u),np.array(row.SOVI_SCORE/100),design,spec["designs"][design]["common_chroma_factors_at_257_burden_knots"])
        else:
            t=row.SOVI_SCORE/100 if scalar=="SOVI" else u
            rgb=linear_to_srgb(lab_to_linear(np.array([91-49*t,0.,0.])))
        selected.append(drawing_code(d,rgb))
    selected.extend(drawing_code(d) for kind in ["NA","high_high"] for d in paths[kind])
    x0,y0,x1,y1=paths["map_clip"]
    append_content(page,f"q 1 0 0 -1 0 {H} cm {x0} {y0} {x1-x0} {y1-y0} re W n\n"+"".join(selected)+"Q")
    legends(page,spec,design,scalar=scalar)
    return doc


def compose(source,canvas):
    # Remove superseded D legend text in a private copy before clipping it away.
    clean=fitz.open(stream=source.tobytes(),filetype="pdf")
    clean[0].add_redact_annot(fitz.Rect(D_RECT),fill=None)
    clean[0].apply_redactions(images=0,graphics=0)
    out=fitz.open();p=out.new_page(width=W,height=H)
    top=fitz.Rect(0,0,W,425.)
    left=fitz.Rect(0,425.,259.2,H)
    p.show_pdf_page(top,clean,0,clip=top,keep_proportion=False)
    p.show_pdf_page(left,clean,0,clip=left,keep_proportion=False)
    p.show_pdf_page(fitz.Rect(D_RECT),canvas,0,clip=fitz.Rect(D_RECT),keep_proportion=False)
    out.set_metadata({"title":"Figure 7. Community recovery types and social vulnerability",
                      "subject":"Visualization-only experimental D; A-C imported unchanged from October14 authority"})
    return out


def export(doc,name,dpi=600):
    write(name+".pdf",doc.tobytes(garbage=4,deflate=True,no_new_id=True))
    for i,p in enumerate(doc):
        suffix="" if len(doc)==1 else f"_{i+1:02d}"
        p.get_pixmap(dpi=dpi,alpha=False).save(str(lp(HERE/(name+suffix+".png"))))


def crop_panel(source):
    rect=fitz.Rect(PANEL_RECT)
    d=fitz.open();p=d.new_page(width=2*rect.width,height=2*rect.height)
    p.show_pdf_page(p.rect,source,0,clip=rect,keep_proportion=False)
    return d


def main():
    spec=audit();f,_=inputs()
    source=fitz.open(lp(HERE/"inputs/FIGURE7_APPROVED.pdf"))
    paths=json.loads(np.load(lp(HERE/"inputs/SOURCE_D_VECTOR_PATHS.npz"))["payload"].tobytes())
    canvases={design:panel_canvas(spec,design,paths,f) for design in DESIGNS}
    candidates={design:compose(source,canvas) for design,canvas in canvases.items()}
    primary=candidates["blue_amber"]
    export(primary,"FIGURE7_CONTINUOUS_REVIEW")
    enlarged=crop_panel(primary);export(enlarged,"FIGURE7D_CONTINUOUS")
    # One proof page preserves the physical size of each complete figure.
    comparison=fitz.open();p=comparison.new_page(width=2*W,height=H+30)
    font(p);text(p,(W/2,17),"Approved October 14 design",size=10,bold=True,align="center")
    text(p,(1.5*W,17),"Continuous SOVI and recovery burden",size=10,bold=True,align="center")
    p.show_pdf_page(fitz.Rect(0,30,W,H+30),source,0,keep_proportion=False)
    p.show_pdf_page(fitz.Rect(W,30,2*W,H+30),primary,0,keep_proportion=False)
    # The second page compares all three D encodings at native publication size.
    pr=fitz.Rect(PANEL_RECT);p=comparison.new_page(width=3*pr.width,height=pr.height+30)
    font(p)
    for j,(label,doc) in enumerate([("Original categorical-continuous",source),("Continuous blue-amber",primary),("Continuous teal-wine",candidates["teal_wine"]) ]):
        text(p,((j+.5)*pr.width,16),label,size=9,bold=True,align="center")
        p.show_pdf_page(fitz.Rect(j*pr.width,30,(j+1)*pr.width,30+pr.height),doc,0,clip=pr,keep_proportion=False)
    export(comparison,"ORIGINAL_VS_CONTINUOUS_COMPARISON",dpi=300)
    # Enlarged continuous legends use the exact same PDF function shading.
    legendbook=fitz.open()
    for design in ["blue_amber","teal_wine"]:
        p=legendbook.new_page(width=W,height=290);font(p)
        text(p,(W/2,20),"Continuous recovery burden and social vulnerability",size=11,bold=True,align="center")
        text(p,(W/2,37),design.replace("_","-"),size=9,align="center")
        uu,vv=np.meshgrid(np.linspace(0,1,129),np.linspace(0,1,129))
        rgb=color(uu,vv,design,spec["designs"][design]["common_chroma_factors_at_257_burden_knots"])
        rect=(120.,60.,455.,225.)
        shade(p,rect,rgb,"LargeContinuousGradient")
        p.draw_rect(fitz.Rect(rect),color=(.2,.2,.2),width=.5)
        lo,hi=spec["burden_normalization"]["minimum_hr"],spec["burden_normalization"]["maximum_hr"]
        for value in [25,35,45,50]:
            px=rect[0]+(value-lo)/(hi-lo)*(rect[2]-rect[0])
            p.draw_line((px,rect[3]),(px,rect[3]+3),color=(.2,.2,.2),width=.5)
            text(p,(px,rect[3]+15),str(value),size=10,align="center")
        for value in [0,25,50,75,100]:
            py=rect[3]-value/100*(rect[3]-rect[1])
            p.draw_line((rect[0]-3,py),(rect[0],py),color=(.2,.2,.2),width=.5)
            width=fitz.Font(fontfile=str(FONT)).text_length(str(value),fontsize=10)
            text(p,(rect[0]-7-width,py+3),str(value),size=10)
        ylabel="SOVI score (0-100)"
        length=fitz.Font(fontfile=str(FONT)).text_length(ylabel,fontsize=10)
        text(p,(78,(rect[1]+rect[3]+length)/2),ylabel,size=10,rotate=90)
        text(p,((rect[0]+rect[2])/2,264),"Equivalent service-deficit hours",size=10,align="center")
    export(legendbook,"CONTINUOUS_2D_LEGENDS",dpi=600)
    # Separate maps retain each original map's native geographic dimensions.
    separate=fitz.open();p=separate.new_page(width=2*pr.width,height=pr.height)
    for j,(kind,label) in enumerate([("SOVI","Social vulnerability"),("burden","Recovery burden")]):
        canvas=panel_canvas(spec,"blue_amber",paths,f,scalar=kind)
        font(canvas[0]);text(canvas[0],(394,420),label,size=9.5,bold=True,align="center")
        p.show_pdf_page(fitz.Rect(j*pr.width,0,(j+1)*pr.width,pr.height),canvas,0,clip=pr,keep_proportion=False)
    export(separate,"ALIGNED_SEPARATE_MAPS",dpi=600)
    # Render actual PDF panels, not an alternate plotting canvas.
    rows=[];preview=lp(HERE/"previews");preview.mkdir(exist_ok=True)
    fonts=ImageFont.truetype(str(FONT),15)
    for label,doc in [("Original",source),("Continuous blue-amber",primary),("Continuous teal-wine",candidates["teal_wine"])]:
        pix=doc[0].get_pixmap(dpi=150,clip=pr,alpha=False)
        rgb=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)/255
        images=[]
        stem=label.lower().replace(" ","_").replace("-","_")
        for mode in ["normal","grayscale",*MACHADO]:
            displayed=rgb if mode=="normal" else simulate(rgb,mode)
            image=Image.fromarray(np.rint(displayed*255).astype(np.uint8))
            image.save(str(preview/(stem+"_"+mode+".png")));images.append(image)
        rows.append((label,images))
    iw,ih=rows[0][1][0].size
    montage=Image.new("RGB",(5*iw,3*(ih+30)),"white");draw=ImageDraw.Draw(montage)
    for i,(label,images) in enumerate(rows):
        for j,(mode,image) in enumerate(zip(["Normal","Grayscale",*MACHADO],images)):
            x,y=j*iw,i*(ih+30)
            draw.text((x+6,y+5),label+": "+mode,font=fonts,fill="black")
            montage.paste(image,(x,y+30))
    montage.save(str(lp(HERE/"ACCESSIBILITY_COMPARISON.png")))
    # Exact A-C pixel invariance at native and high-resolution export sizes.
    pixel=[]
    for dpi in [150,300,600]:
        original=source[0].get_pixmap(dpi=dpi,alpha=False)
        old=np.frombuffer(original.samples,dtype=np.uint8).reshape(original.height,original.width,3)
        for design,doc in candidates.items():
            rendered=doc[0].get_pixmap(dpi=dpi,alpha=False)
            new=np.frombuffer(rendered.samples,dtype=np.uint8).reshape(rendered.height,rendered.width,3)
            x=int(np.floor(D_RECT[0]*dpi/72));y=int(np.floor(D_RECT[1]*dpi/72))
            count=int(np.count_nonzero(old[:y]!=new[:y])+np.count_nonzero(old[y:,:x]!=new[y:,:x]))
            assert count==0,(design,dpi,count)
            pixel.append({"design":design,"dpi":dpi,"A_B_C_changed_color_channels":count})
    save("ABC_PIXEL_PRESERVATION.csv",pixel)
    dump("BUILD_QA.json",{"status":"PASS","primary_continuous_palette":"blue_amber","publication_figure_width_inches":W/72,
        "publication_figure_height_inches":H/72,"only_modified_region_pt":D_RECT,
        "A_C_pixel_identical_at_dpi":[150,300,600],"source_map_clip_pt":paths["map_clip"],
        "data_bins_used":0,"source_geography_paths_replayed":len(paths["positive"]),"NA_paths":len(paths["NA"]),
        "high_high_paths":len(paths["high_high"]),"source_high_high_linewidth_pt":paths["high_high"][0]["width"],
        "new_text_minimum_points_in_full_figure":7.5,"no_official_artifact_replaced":True})
    print("Five vector PDFs and actual-size/accessibility proofs built; A-C pixel-identical at150/300/600dpi.")


if __name__=="__main__":main()
