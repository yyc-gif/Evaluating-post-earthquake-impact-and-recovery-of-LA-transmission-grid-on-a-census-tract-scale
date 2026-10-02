"""Layout-only adapter for the frozen candidate_v2.1 presentation renderer.

The source renderer constructs each plot using its existing metric, strategy,
reference, data and statistical definitions. This adapter changes physical axes
positions and visual properties immediately before export. It neither calls a
physical experiment nor writes scientific tables or the publication collection.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import shutil
import textwrap
from pathlib import Path

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.container import ErrorbarContainer
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.transforms import ScaledTranslation
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SOURCE = OUT.parent / "candidate_v2.1"
SPEC = importlib.util.spec_from_file_location("accepted_v21_layout_source", SOURCE / "build_candidate_v2_1.py")
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)
base = v.base
WIDTH = 185.0
TITLE, LABEL, TICK, LEGEND = 9.5, 8.5, 7.5, 7.5
FONT = "Arial"
HAZARD_COLORS = {"Long Beach": "#366E9F", "San Fernando": "#9364A1",
                 "Northridge": "#9a7559", "2pc50": "#a65628"}
RECORDS, QA = [], []
PLOT_SIGNATURES = {}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def all_axes(fig):
    found = []
    def visit(ax):
        if ax in found:
            return
        found.append(ax)
        for child in ax.child_axes:
            visit(child)
    for ax in fig.axes:
        visit(ax)
    return found


def data_signature(fig):
    """Hash plotted values/geometry/limits; deliberately exclude visual style."""
    h = hashlib.sha256()
    def array(x):
        a = np.asanyarray(x)
        h.update(str(a.shape).encode())
        h.update(str(a.dtype).encode())
        if a.dtype.hasobject or a.dtype.kind in "US":
            h.update(repr(a.tolist()).encode())
        else:
            h.update(np.ascontiguousarray(a).tobytes())
        if np.ma.isMaskedArray(a):
            array(np.ma.getmaskarray(a))
    for ax in fig.axes:
        array(ax.get_xlim()); array(ax.get_ylim())
        for line in ax.lines:
            array(line.get_xdata()); array(line.get_ydata())
        for col in ax.collections:
            array(col.get_offsets())
            if col.get_array() is not None:
                array(col.get_array())
            for p in col.get_paths():
                array(p.vertices)
                if p.codes is not None:
                    array(p.codes)
        for im in ax.images:
            array(im.get_array()); array(im.get_extent())
        for patch in ax.patches:
            if isinstance(patch, matplotlib.patches.FancyArrowPatch):
                # Arrowhead geometry is computed in physical display points;
                # resizing the diagram may change it without changing data.
                continue
            array(patch.get_path().vertices)
            # Data transforms remain unchanged by physical axes positioning.
            if hasattr(patch, "get_x"):
                array([patch.get_x(), patch.get_y(), patch.get_width(), patch.get_height()])
    return h.hexdigest()


def box(fig, ax, x, top, w, h):
    height = fig.get_figheight() * 25.4
    ax.set_position([x / WIDTH, (height - top - h) / height, w / WIDTH, h / height])


def title_at(fig, ax, x, top, text=None, size=TITLE):
    label = text if text is not None else ax.get_title(loc="left") or ax.get_title()
    ax.set_title("", loc="left"); ax.set_title("")
    if label:
        fig.text(x / WIDTH, 1 - top / (fig.get_figheight() * 25.4), label,
                 ha="left", va="bottom", fontsize=size, fontweight="bold", fontfamily=FONT)


def resize_keep_positions(fig, height):
    old_height = fig.get_figheight() * 25.4
    pos = [(ax, ax.get_position(original=True).frozen()) for ax in fig.axes]
    fig.set_size_inches(WIDTH / 25.4, height / 25.4, forward=True)
    for ax, p in pos:
        box(fig, ax, p.x0 * WIDTH, (1 - p.y1) * old_height,
            p.width * WIDTH, p.height * old_height)


def remove_footer_notes(fig):
    # These explanations already appear verbatim in the unchanged captions.
    for t in list(fig.texts):
        if t.get_position()[1] < .16 and not t.get_fontweight() == "bold":
            t.remove()


def common_style(fig):
    for t in fig.findobj(match=Text):
        if t.get_text():
            text = t.get_text()
            text = text.replace("Simplified retained topology", "Simplified network topology")
            text = text.replace("Retained grid stations", "Modeled substations")
            text = text.replace("Retained sequence identity", "Selected sequence identity")
            text = text.replace("Retained:", "Selected:")
            t.set_text(text)
            t.set_fontfamily(FONT)
            t.set_fontsize(max(7.0, t.get_fontsize()))
    for ax in all_axes(fig):
        ax.xaxis.label.set_fontsize(LABEL)
        ax.yaxis.label.set_fontsize(LABEL)
        ax.tick_params(axis="both", labelsize=TICK, width=.6)
        for sp in ax.spines.values():
            sp.set_linewidth(.6)
        for t in [ax.title, ax._left_title, ax._right_title]:
            t.set_fontsize(TITLE)
            t.set_fontweight("bold")
        for line in ax.get_xgridlines() + ax.get_ygridlines():
            line.set_linewidth(.4)
        for container in ax.containers:
            if isinstance(container, ErrorbarContainer):
                data, caps, bars = container.lines
                if data is not None:
                    data.set_markersize(3.2)
                for cap in caps:
                    cap.set_markersize(4.0); cap.set_markeredgewidth(.75)
                for bar in bars:
                    bar.set_linewidth(.75)
        leg = ax.get_legend()
        if leg:
            for t in leg.get_texts():
                t.set_fontsize(LEGEND); t.set_fontfamily(FONT)
            leg.set_frame_on(False)
    for leg in fig.legends:
        for t in leg.get_texts():
            t.set_fontsize(LEGEND); t.set_fontfamily(FONT)
        leg.set_frame_on(False)


def legend(fig, handles, x, top, ncol=3, labels=None, loc="upper center"):
    if labels is None:
        labels = [handle.get_label() for handle in handles]
    return fig.legend(handles, labels, frameon=False, ncol=ncol, loc=loc,
                      bbox_to_anchor=(x / WIDTH, 1 - top / (fig.get_figheight() * 25.4)),
                      fontsize=LEGEND, columnspacing=1.1, handletextpad=.4,
                      labelspacing=.35, handlelength=1.8, borderaxespad=0)


def policy_handles(keys, lines=True):
    return [Line2D([0], [0], color=v.STYLE[k][0], ls=v.STYLE[k][1] if lines else "-",
                   lw=1.2 if lines else 0, marker="o", ms=3.2,
                   label=v.POLICY_LABEL[k]) for k in keys]


def layout_02(fig):
    axes = fig.axes[:4]
    p = axes[3].get_position(original=True)
    box(fig, axes[3], 120, (1-p.y1)*174, 59, p.height*174)
    axes[3].set_xlabel("Agreement with public-site\nevidence (%)")
    for text in axes[3].texts:
        if text.get_text().endswith("%"):
            text.set_transform(text.get_transform() + ScaledTranslation(3/72, 0, fig.dpi_scale_trans))
    # Keep the balanced 2x2, original geography and all agreement values.
    for ax, x, top in zip(axes, [9, 101, 9, 101], [10, 10, 84, 84]):
        title_at(fig, ax, x, top)
    for ax in axes[:2]:
        lg = ax.get_legend()
        if lg:
            lg.set_loc("upper center")
            lg.set_bbox_to_anchor((.5, -.02))
    for ax in axes:
        leg = ax.get_legend()
        if leg:
            leg.set_frame_on(False)
    return "2x2 kept; topology/station wording clarified; public-site values offset 3 pt from points; letters and legends aligned"


def layout_03(fig):
    a, b, c, d, mp = fig.axes[:5]
    box(fig, a, 24, 18, 62, 44)
    box(fig, b, 109, 18, 70, 44)
    box(fig, c, 24, 94, 155, 31)
    box(fig, d, 24, 149, 56, 52)
    box(fig, mp, 91, 149, 88, 52)
    for patch, hazard in zip(a.patches, base.HAZARDS):
        patch.set_facecolor(HAZARD_COLORS[base.HAZARD_LABEL[hazard]])
        patch.set_alpha(.80)
    for line in b.lines:
        name = line.get_label()
        line.set_color(HAZARD_COLORS[name])
        line.set_linestyle({"Long Beach":"-", "San Fernando":"--", "Northridge":"-.", "2pc50":"-"}[name])
        line.set_zorder(5)
        if name == "2pc50":
            line.set_linewidth(1.4)
            line.set_clip_on(False)
    # Move the visible frame, not the data or probability limits, away from
    # the steep 2pc50 CDF at x=0 and from the upper probability boundary.
    b.spines["left"].set_position(("outward", 3))
    for spine in b.spines.values(): spine.set_zorder(0)
    handles, labels = b.get_legend_handles_labels()
    b.legend(handles, labels, frameon=False, loc="lower right", ncol=2, fontsize=LEGEND)
    d.set_title("D. 2pc50 Unconstrained T80", loc="left")
    d.set_ylabel("2pc50 realizations (n)")
    for ax, x, top in [(a,24,14),(b,109,14),(c,24,82),(d,24,143)]:
        title_at(fig, ax, x, top)
    # Map title becomes a fixed row anchor, independent of map aspect fitting.
    mt = mp.texts[0]
    text = mt.get_text(); mt.remove()
    fig.text(91 / WIDTH, 1 - 143 / 216, text, ha="left", va="bottom",
             fontsize=TITLE, fontweight="bold", fontfamily=FONT)
    c_handles, c_labels = c.get_legend_handles_labels()
    c.get_legend().remove()
    legend(fig, c_handles, 101, 85, ncol=3, labels=c_labels)
    # Preserve every T80 value and scale; use a standard 2.2-mm bar thickness.
    cax = mp.child_axes[0]
    cax.set_axes_locator(None)
    box(fig, cax, 103, 205, 60, 2.2)
    d.set_xlabel("Population-weighted time to\n80% service (h)")
    return "Long Beach blue / San Fernando purple with distinct line styles; 2pc50 CDF drawn above offset frame; histogram scenario explicit; baseline layout kept"


def layout_04(fig):
    a, *outcomes = fig.axes
    remove_footer_notes(fig)
    for t in list(a.texts):
        if "Curve display" in t.get_text():
            t.remove()
    box(fig, a, 36, 18, 143, 66)
    title_at(fig, a, 36, 13)
    handles, labels = a.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    a.get_legend().remove()
    order = [*base.POLICIES_4, "centrality-first", "betweenness-first", "closeness-first", "random", "unconstrained"]
    leg = legend(fig, [by_label[v.POLICY_LABEL[k]] for k in order], 106, 99,
                 ncol=3, labels=[v.POLICY_LABEL[k] for k in order])
    for key, text in zip(order, leg.get_texts()):
        text.set_fontweight("bold" if key in v.CORE_POLICIES or key == "unconstrained" else "normal")
    for line in a.lines:
        key = next(k for k in v.STRATEGY_ORDER if v.POLICY_LABEL[k] == line.get_label())
        core = key in v.CORE_POLICIES or key == "unconstrained"
        line.set_alpha(1.0 if core else .40)
        line.set_linewidth(1.4 if key in v.CORE_POLICIES else 1.15 if key == "unconstrained" else .8)
        line.set_zorder(4 if core else 2)
    a.set_xlabel("Time after earthquake (h)")
    a.set_ylabel("Mean population-weighted\nservice availability")
    for j, ax in enumerate(outcomes):
        box(fig, ax, 36 + j * 36, 132, 27, 56)
        ax.set_title("", loc="left"); ax.set_title("")
        ax.set_xlabel(ax.get_xlabel().replace(" (h)", "\n(h)"))
        for key, cont in zip(v.STRATEGY_ORDER, ax.containers):
            if isinstance(cont, ErrorbarContainer):
                alpha = 1.0 if key in v.CORE_POLICIES or key == "unconstrained" else .50
                for artist in [cont.lines[0], *cont.lines[1], *cont.lines[2]]:
                    if artist is not None: artist.set_alpha(alpha)
                if cont.lines[0] is not None:
                    cont.lines[0].set_markersize(3.2 if alpha == 1 else 2.7)
    fig.text(36/WIDTH, 1-126/205, "B. Outcome ranges", fontsize=TITLE,
             weight="bold", ha="left", va="bottom", fontfamily=FONT)
    return "all nine identities retained; core policies emphasized; shared external legend; repeated column titles removed; notes left in unchanged caption"


def layout_05(fig):
    a,b,bleg,ctitle,rleg,c,g,d,holder = fig.axes[:9]
    old_map = d.get_position().frozen()
    map_width, map_height = old_map.width * WIDTH, old_map.height * 218
    fig.set_size_inches(WIDTH/25.4, 208/25.4, forward=True)
    for lg in list(fig.legends): lg.remove()
    if bleg.get_legend(): bleg.get_legend().remove()
    if rleg.get_legend(): rleg.get_legend().remove()
    # Keep the helper axes and their data (none); just silence repeated keys.
    for t in list(ctitle.texts): t.remove()
    for helper in (bleg,ctitle,rleg): helper.set_visible(False)
    legend(fig, policy_handles(v.STRATEGY_ORDER), 105, 4, ncol=3)
    box(fig, a, 36, 28, 143, 21)
    box(fig, b, 36, 64, 143, 23)
    box(fig, c, 36, 109, 103, 26)
    box(fig, g, 157, 109, 22, 26)
    # The map's actual width and height are retained; excess outer white space
    # comes from repeated legends and row gutters, never from map downscaling.
    map_h = max(47.0, map_height)
    map_w = max(100.0, map_width)
    box(fig, d, 47, 155, map_w, map_h)
    box(fig, holder, 165, 155, 10, map_h)
    title_at(fig, a, 36, 23)
    title_at(fig, b, 36, 59)
    fig.text(36/WIDTH,1-103/208,"C. Vulnerability-first change relative to matched policies",
             ha="left",va="bottom",fontsize=TITLE,fontweight="bold",fontfamily=FONT)
    title_at(fig, g, 157, 103, text="D. Gini change", size=TITLE)
    g.set_xticks([-.025, 0, .025], ["−0.025", "0", "0.025"])
    title_at(fig, d, 36, 149,
             text="E. Mean tract burden change: Vulnerability-first − Impact-first")
    cax = holder.child_axes[0]
    cax.set_axes_locator(None); box(fig, cax, 166, 164, 2.2, 34)
    return "218 to 208 mm; shared legend; Gini identified as D and tract map as E; map physical size unchanged; colorbar aligned"


def wrap_label(ax, text, width=31):
    # Whitespace-only wrapping; no metric name or unit changes.
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False))


def layout_06(fig):
    remove_footer_notes(fig)
    for lg in list(fig.legends): lg.remove()
    legend(fig, policy_handles(base.POLICIES_4, lines=False), 104, 7, ncol=4)
    for ax in fig.axes:
        title_at(fig, ax, ax.get_position(original=True).x0 * WIDTH,
                 (1-ax.get_position(original=True).y1)*169 - 4,
                 text="\n".join(textwrap.wrap(ax.get_title(loc="left"), 37, break_long_words=False, break_on_hyphens=False)))
        ax.set_ylabel(wrap_label(ax, ax.get_ylabel(), 31))
    return "consistent crew-category positions/offsets retained in all panels; long labels wrapped; legend/font/interval style unified; footer note moved to existing caption"


def layout_07(fig):
    profile, profile_bar, cluster, hotspot = fig.axes[:4]
    box(fig, profile, 35, 11, 130, 54)
    box(fig, profile_bar, 168, 11, 2.2, 54)
    box(fig, cluster, 35, 88, 60, 68)
    box(fig, hotspot, 108, 88, 60, 68)
    for ax in fig.axes:
        if ax.get_title(loc="left"):
            p = ax.get_position(original=True)
            title_at(fig, ax, p.x0*WIDTH, (1-p.y1)*188-4)
    # The source's cluster-ID palette and N/A hatching are untouched.
    cax = hotspot.child_axes[0]
    p = hotspot.get_position()
    cax.set_axes_locator(None)
    box(fig,cax,170, (1-p.y1)*188+7,2.2,34)
    return "cluster/profile/hotspot structure retained; cluster-ID palette unchanged; map colorbar aligned; panel title and legend hierarchy unified"


def layout_support(fig, stem):
    remove_footer_notes(fig)
    if "Cross_Hazard" in stem:
        resize_keep_positions(fig, 198)
    elif "Crew_Resource_Contrasts" in stem or "Repair_Duration_Contrasts" in stem:
        resize_keep_positions(fig, 180)
        for ax in fig.axes:
            if ax.get_ylabel():
                ax.set_ylabel(wrap_label(ax,ax.get_ylabel()))
            title = ax.get_title(loc="left")
            if title:
                ax.set_title("\n".join(textwrap.wrap(title, 38, break_long_words=False,
                                                      break_on_hyphens=False)), loc="left")
    return "caption-only boundary notes removed from artwork; shared font/legend/interval hierarchy; physical whitespace reduced where safe"


LAYOUTS = {"Fig02":layout_02,"Fig03":layout_03,"Fig04":layout_04,
           "Fig05":layout_05,"Fig06":layout_06,"Fig07":layout_07}


def pdf_qa(path):
    with fitz.open(path) as doc:
        page=doc[0]
        spans=[s for b in page.get_text("dict")["blocks"] if "lines" in b
               for ln in b["lines"] for s in ln["spans"] if s["text"].strip()]
        fonts=sorted({f[3] for f in page.get_fonts(full=True)})
        outside=[s["text"] for s in spans if s["bbox"][0]<-.5 or s["bbox"][1]<-.5
                 or s["bbox"][2]>page.rect.width+.5 or s["bbox"][3]>page.rect.height+.5]
        dpi=[]
        for im in page.get_image_info():
            x0,y0,x1,y1=im["bbox"]
            if x1>x0 and y1>y0:
                dpi.append(min(im["width"]*72/(x1-x0),im["height"]*72/(y1-y0)))
        return {"file":path.name,"width_mm":page.rect.width/72*25.4,
                "height_mm":page.rect.height/72*25.4,
                "minimum_text_pt":min([s["size"] for s in spans],default=0),
                "fonts":";".join(fonts),"text_outside_page":len(outside),
                "outside_text":"; ".join(outside),"min_embedded_raster_dpi":min(dpi) if dpi else None}


def save_layout(fig, stem):
    fig.canvas.draw()
    before_signature = data_signature(fig)
    before_h=fig.get_figheight()*25.4
    original_map_area = None
    if stem.startswith("Fig05"):
        p=fig.axes[7].get_position()
        original_map_area=(p.width*WIDTH,p.height*before_h)
    common_style(fig)
    if stem.startswith("Fig01"):
        ax=fig.axes[0]
        for t in list(ax.texts):
            if t.get_position()[1] < .20: t.remove()
            elif len(t.get_text()) > 29 and "\n" not in t.get_text():
                t.set_text("\n".join(textwrap.wrap(t.get_text(), 27, break_long_words=False)))
        resize_keep_positions(fig,78)
        action="footer explanations left in unchanged caption; bottom whitespace cropped; diagram geometry and text retained"
    elif stem[:5] in LAYOUTS:
        action=LAYOUTS[stem[:5]](fig)
    else:
        action=layout_support(fig,stem)
    common_style(fig)
    # Restore the deliberate Fig04 emphasis after the shared interval styling.
    if stem.startswith("Fig04"):
        for ax in fig.axes[1:]:
            for key,cont in zip(v.STRATEGY_ORDER,ax.containers):
                if isinstance(cont,ErrorbarContainer) and cont.lines[0] is not None:
                    cont.lines[0].set_markersize(3.2 if key in v.CORE_POLICIES or key=="unconstrained" else 2.7)
    fig.canvas.draw()
    after_signature=data_signature(fig)
    if before_signature != after_signature:
        raise ValueError(f"Plotted scientific values/geometry/limits changed: {stem}")
    PLOT_SIGNATURES[stem] = {"before":before_signature,"after":after_signature,"equal":True}
    map_width=map_height=None
    if original_map_area:
        p=fig.axes[7].get_position(); map_width=p.width*WIDTH;map_height=p.height*fig.get_figheight()*25.4
        if map_width+0.1<original_map_area[0] or map_height+0.1<original_map_area[1]:
            raise ValueError(f"Fig05 map shrank: {original_map_area} -> {(map_width,map_height)}")
    pdf=OUT/f"{stem}.pdf"; png=OUT/f"{stem}.png"
    meta={"Title":stem.replace("_"," "),"Author":"Candidate v2.1 layout-only review"}
    fig.savefig(pdf,dpi=600,facecolor="white",metadata=meta)
    fig.savefig(png,dpi=600,facecolor="white")
    fig.savefig(OUT/f"{stem}_preview.png",dpi=150,facecolor="white")
    plt.close(fig)
    qa=pdf_qa(pdf); QA.append(qa)
    if qa["minimum_text_pt"]<6.99 or qa["text_outside_page"]:
        raise ValueError(f"Final-size text QA failed: {qa}")
    RECORDS.append({"figure":stem,"before_height_mm":round(before_h,1),
                    "after_height_mm":round(qa["height_mm"],1),"visual_changes":action,
                    "scientific_content_changed":"NO", "map_before_width_mm":original_map_area[0] if original_map_area else None,
                    "map_before_height_mm":original_map_area[1] if original_map_area else None,
                    "map_after_width_mm":map_width,"map_after_height_mm":map_height})
    print(stem, f"{before_h:.0f} -> {qa['height_mm']:.0f} mm",flush=True)
    return pdf,png,OUT/f"{stem}_preview.png"


def page_previews():
    """A4, actual 185-mm placement; artwork is never reduced to fit the page."""
    packet=fitz.open()
    arial=Path("C:/Windows/Fonts/arial.ttf")
    for stem,caption in v.CAPTIONS.items():
        with fitz.open(OUT/f"{stem}.pdf") as src:
            page=packet.new_page(width=210/25.4*72,height=297/25.4*72)
            page.insert_font(fontname="LocalArial",fontfile=str(arial))
            h=src[0].rect.height
            left=12.5/25.4*72;top=18/25.4*72
            page.insert_text((left,11/25.4*72),stem.replace("_"," "),fontname="LocalArial",fontsize=8)
            # Native PDF placement at 1:1 scale, not a PNG inside a PDF.
            page.show_pdf_page(fitz.Rect(left,top,left+src[0].rect.width,top+h),src,0)
            brief=caption.split(". ",1)[0]+". Full caption in the review packet."
            y=top+h+7/25.4*72
            if y+35>page.rect.height-12/25.4*72:
                raise ValueError(f"Figure does not fit typical page at actual width: {stem}")
            result=page.insert_textbox(fitz.Rect(left,y,page.rect.width-left,y+35),brief,
                                      fontname="LocalArial",fontsize=8.5,lineheight=1.2)
            if result<0: raise ValueError(f"Page-preview caption overflow: {stem}")
            pix=page.get_pixmap(matrix=fitz.Matrix(150/72,150/72),alpha=False)
            pix.save(OUT/f"{stem}_page_preview.png")
    packet.save(OUT/"LAYOUT_JOURNAL_PAGE_PREVIEWS.pdf",garbage=4,deflate=True)
    packet.close()


def review_packet():
    out=fitz.open()
    # Preserve unaffected caption pages; synchronize edited display wording
    # and panel references without changing the scientific definitions.
    with fitz.open(SOURCE/"FIGURE_V2_1_REVIEW_PACKET.pdf") as old:
        for i,stem in enumerate(v.CAPTIONS):
            with fitz.open(OUT/f"{stem}.pdf") as src: out.insert_pdf(src)
            if stem.startswith(("Fig02", "Fig04", "Fig05")):
                page = out.new_page(width=185/25.4*72, height=340/25.4*72)
                page.insert_font(fontname="LocalArial", fontfile="C:/Windows/Fonts/arial.ttf")
                page.insert_text((24, 32), stem.replace("_", " "), fontname="LocalArial", fontsize=9.5)
                available = page.insert_textbox(fitz.Rect(24, 56, page.rect.width-24, page.rect.height-24),
                                                v.CAPTIONS[stem], fontname="LocalArial", fontsize=9.5, lineheight=1.25)
                if available < 0: raise ValueError(f"Updated caption does not fit: {stem}")
            else:
                out.insert_pdf(old,from_page=2*i+1,to_page=2*i+1)
    out.save(OUT/"FIGURE_V2_1_LAYOUT_REVIEW_PACKET.pdf",garbage=4,deflate=True)
    out.close()


def contact_sheets():
    for n,start in enumerate(range(0,len(v.CAPTIONS),4),start=1):
        sheet=Image.new("RGB",(1600,1800),"#e8ebed")
        for j,stem in enumerate(list(v.CAPTIONS)[start:start+4]):
            im=Image.open(OUT/f"{stem}_preview.png").convert("RGB")
            im.thumbnail((760,820),Image.Resampling.LANCZOS)
            tile=Image.new("RGB",(790,890),"white")
            ImageDraw.Draw(tile).text((12,12),stem.replace("_"," "),fill="#283b44")
            tile.paste(im,((790-im.width)//2,45));sheet.paste(tile,((j%2)*800,(j//2)*900))
        sheet.save(OUT/f"LAYOUT_CONTACT_SHEET_{n:02d}.png",dpi=(150,150))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source_rows=pd.read_csv(SOURCE/"FIGURE_V2_1_SOURCE_HASHES.csv")
    sources={ROOT/r.source_path:r.sha256 for r in source_rows.itertuples()}
    mismatches=[str(p) for p,h in sources.items() if sha(p)!=h]
    if mismatches: raise ValueError(f"Frozen source identity differs from v2.1: {mismatches}")
    originals={p:sha(p) for p in SOURCE.iterdir() if p.is_file()}
    formal_figures={p:sha(p) for p in (ROOT/"results"/"figures").iterdir() if p.is_file()}
    v.save_figure=save_layout;base.save_figure=save_layout
    eval_data=base.read_eval();tracts=base.map_domain()
    base.build_fig01();v.build_fig02();v.build_fig03(eval_data);base.build_fig04(eval_data)
    v.build_fig05(eval_data,tracts);v.build_fig06(eval_data);v.build_fig07()
    v.build_figs05();v.build_figs09()
    effects=pd.read_csv(SOURCE/"CROSS_HAZARD_POLICY_EFFECTS.csv")
    v.build_cross_hazard(None,effects)
    v.build_discrete_case_figure(eval_data,"crew");v.build_discrete_case_figure(eval_data,"duration")
    # Reader-facing nomenclature and panel references only; caption science
    # and statistical statements retain the original definitions.
    for stem in v.CAPTIONS:
        caption = v.CAPTIONS[stem]
        if stem.startswith("Fig02"):
            caption = caption.replace("the retained model graph", "the model network")
        elif stem.startswith("Fig04"):
            caption = caption.replace("mean population service availability", "mean population-weighted service availability")
        elif stem.startswith("Fig05"):
            caption = caption.replace("population-weighted Gini change uses a separate unitless axis.",
                                      "(D) Population-weighted Gini change uses a separate unitless axis for the same matched comparisons.")
            caption = caption.replace("hour axis; (D)", "hour axis. (D)")
            caption = caption.replace("(D) Tract-level", "(E) Tract-level")
        v.CAPTIONS[stem] = caption
    page_previews();review_packet();contact_sheets()
    for name in ["FIGURE_V2_1_PANEL_CROSSWALK.csv",
                 "FIGURE_V2_1_SOURCE_HASHES.csv","STORY_EVIDENCE_MATRIX.md","CROSS_HAZARD_POLICY_EFFECTS.csv"]:
        shutil.copyfile(SOURCE/name,OUT/name)
    (OUT/"FIGURE_V2_1_CAPTIONS.md").write_text("# Figure v2.1 layout draft captions\n\n"+
        "\n\n".join(f"## {stem}\n\n{caption}" for stem, caption in v.CAPTIONS.items())+"\n", encoding="utf-8")
    crosswalk = pd.read_csv(OUT/"FIGURE_V2_1_PANEL_CROSSWALK.csv")
    # Keep source/metric identity and change only the existing map locator.
    crosswalk = crosswalk.replace("Fig05-D", "Fig05-E")
    gini = crosswalk[crosswalk.candidate_v2_1_panel_id.eq("Fig05-C")].iloc[0].copy()
    gini["panel_id"] = "Fig05-D"
    gini["candidate_v2_1_panel_id"] = "Fig05-D"
    gini["metric_definition"] = "Population-weighted Gini: matched VF minus Impact/Hospital/Degree change; mean and 5th-95th paired range"
    gini["interpretation_boundary"] = "Separate labeled unitless axis; 0 is equal tract burden, larger Gini is greater inequality"
    gini["v2_1_change"] = "Existing Gini subplot explicitly lettered D; no metric, data or reference change"
    crosswalk = pd.concat([crosswalk, gini.to_frame().T], ignore_index=True)
    crosswalk.to_csv(OUT/"FIGURE_V2_1_PANEL_CROSSWALK.csv", index=False)
    index=pd.read_csv(SOURCE/"FIGURE_V2_1_INDEX.csv")
    index["caption"] = index.figure_stem.map(v.CAPTIONS)
    index["journal_page_preview"] = index.figure_stem+"_page_preview.png"
    index["layout_review_only"] = True
    index.to_csv(OUT/"FIGURE_V2_1_LAYOUT_INDEX.csv",index=False)
    pd.DataFrame(QA).to_csv(OUT/"LAYOUT_ACTUAL_OUTPUT_QA.csv",index=False)
    pd.DataFrame(RECORDS).to_csv(OUT/"LAYOUT_CHANGELOG.csv",index=False)
    lines=["# Candidate v2.1 layout changelog","", "Scientific content changed = NO.", "",
           "The accepted candidate renderer is reused. Only layout, display wording, panel lettering and colors change. Caption edits clarify the same metric and panel references; scientific source tables and definitions are unchanged.","",
           "| Figure | Height before → after (mm) | Visual changes | Scientific content changed |",
           "|---|---:|---|---|"]
    for r in RECORDS:
        lines.append(f"| {r['figure']} | {r['before_height_mm']:g} → {r['after_height_mm']:g} | {r['visual_changes']} | NO |")
    lines += ["", "Shared hierarchy: Arial; panel title 9.5 pt; axis label 8.5 pt; ticks and legends 7.5 pt; normal text at least 7 pt. Range whiskers retain the original 5th–95th realization definition, using 0.75-pt strokes and consistent caps. Map colorbars use 2.2-mm thickness; vertical map bars use 34-mm height.", "",
              "Figure pages stay at 185 mm. Page previews show each native PDF at actual size on a 210×297-mm two-column page; they are layout review aids, not submission numbering or promotion."]
    (OUT/"LAYOUT_CHANGELOG.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    changed=[str(p) for p,h in {**sources,**originals,**formal_figures}.items() if sha(p)!=h]
    if changed: raise ValueError(f"Protected source/publication files changed: {changed}")
    identity={"source_candidate":"candidate_v2.1","source_commit":"e0153095a69a722cc89e90ecf06790d80e4b4dd4",
              "mode":"layout-only; review; not promoted","figure_count":len(RECORDS),
              "width_mm":WIDTH,"scientific_content_changed":False,"source_hash_changes":0,
              "original_candidate_hash_changes":0,"results_figures_hash_changes":0,
              "captions_identical":sha(OUT/"FIGURE_V2_1_CAPTIONS.md")==sha(SOURCE/"FIGURE_V2_1_CAPTIONS.md"),
              "caption_changes":"display nomenclature and Fig05 D/E references only; scientific meaning unchanged",
              "hazard_display_palette": HAZARD_COLORS,
              "plotted_values_and_geometry":PLOT_SIGNATURES,
              "policy_style":v.STYLE,"cluster_palette":v.get_cluster_palette()[0]}
    (OUT/"LAYOUT_IDENTITY_VALIDATION.json").write_text(json.dumps(identity,indent=2),encoding="utf-8")
    (OUT/"README.md").write_text("# Candidate v2.1 layout review\n\nReview-only derivatives of candidate_v2.1; scientific content changed = NO.\n\nOpen FIGURE_V2_1_LAYOUT_REVIEW_PACKET.pdf for actual-size figures and captions with synchronized display names and panel letters, or LAYOUT_JOURNAL_PAGE_PREVIEWS.pdf for 185-mm placement on typical two-column pages. Each figure has a native PDF, 600-dpi PNG, 150-dpi artwork preview and page preview. See LAYOUT_CHANGELOG.md and LAYOUT_ACTUAL_OUTPUT_QA.csv. Nothing is promoted to results/figures.\n",encoding="utf-8")
    print("LAYOUT_RENDER_COMPLETE: 12 figures; plotted-data parity; source/publication hashes unchanged; caption nomenclature synchronized",flush=True)


if __name__=="__main__":
    main()
