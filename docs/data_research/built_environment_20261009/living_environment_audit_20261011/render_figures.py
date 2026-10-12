"""Native-width measurement diagnostics from actual values; no model fitting."""
from common import *
import pandas as pd,geopandas as gpd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
import fitz
from audit_values import CANDIDATES,CONTEXT,archived_boundaries

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
NAMES={'canopy_2022_fraction':'Urban tree canopy','parks_all_published_fraction':'All Parks proximity','parks_good_published_fraction':'Good Parks proximity','electric_heating_share':'Electric principal heating','housing_5plus_share':'Housing units in 5+ structures','emc2022_total_built_land_fraction':'EMC built-land fraction','log1p_population_density_per_km2':'log1p population density','SOVI_SCORE':'Social vulnerability score'}
SHORT=['Canopy','All\nParks','Good\nParks','Electric\nheating','5+\nhousing','EMC\ncoverage','log1p\ndensity','SOVI']
FOLDER=lp(OUT/'figures');FOLDER.mkdir(exist_ok=True)
def export(pdf,fig,name,page):
    pdf.savefig(fig)
    fig.savefig(FOLDER/f'{name}_page{page}.png',dpi=600)
    plt.close(fig)
def footer(fig,t):fig.text(.04,.025,t,fontsize=8,va='bottom')
def distribution(f):
    ref=f.loc[f.reference2287]
    with PdfPages(FOLDER/'LIVING_ENVIRONMENT_DISTRIBUTIONS.pdf') as pdf:
        fig,axs=plt.subplots(3,2,figsize=(185/25.4,190/25.4))
        fig.subplots_adjust(left=.09,right=.97,bottom=.09,top=.92,hspace=.62,wspace=.32)
        fig.suptitle('Living-environment measurements: reference 2,287 tracts',fontsize=11,y=.982)
        for i,c in enumerate(CANDIDATES):
            ax=axs.flat[i];v=100*ref[c].dropna();upper=50 if i==0 else 100
            # Endpoint storage roundoff is preserved in values; edge bin extends slightly beyond100.
            bins=np.linspace(0,upper+1e-4,21)
            ax.hist(v,bins=bins,color=['#287D8E','#4378A0','#7A7996','#D28A3D','#48789A'][i],edgecolor='white',linewidth=.45)
            ax.axvline(v.median(),color='black',linewidth=.9)
            ax.set(xlim=(0,upper),xlabel='Published proportion (%)' if i in [1,2] else 'Proportion (%)',ylabel='Tracts',title=f'{chr(65+i)}  {NAMES[c]}')
            ax.text(.97,.94,f'Median {v.median():.1f}%',ha='right',va='top',transform=ax.transAxes,fontsize=8)
        ax=axs.flat[5]
        for c,color in [('electric_heating_share','#D28A3D'),('housing_5plus_share','#48789A')]:
            v=np.sort(100*ref[c+'_moe90'].dropna());ax.plot(v,np.arange(1,len(v)+1)/len(v),color=color,lw=1.5,label='Electric heating' if c.startswith('electric') else '5+ housing')
        ax.axvline(10,color='#505050',ls='--',lw=.8);ax.set(xlim=(0,25),ylim=(0,1.02),xlabel='90% MOE (percentage points)',ylabel='Cumulative tract fraction',title='F  ACS sampling uncertainty')
        ax.legend(loc='lower right',frameon=False)
        footer(fig,'Unweighted tract distributions. High-MOE observations retained; parks allocation remains unverified.')
        export(pdf,fig,'LIVING_ENVIRONMENT_DISTRIBUTIONS',1)

def source_canopy():
    fs=[]
    for offset in [0,1000,2000]:fs+=json.loads(lp(OUT/f'sources/CANOPY_LA_{offset}.geojson').read_text())['features']
    return gpd.GeoDataFrame.from_features(fs,crs=4326).to_crs(3310).set_index('FIPS')

def map_pair(pdf,g,panels,name,page,title,note):
    fig,axs=plt.subplots(1,2,figsize=(185/25.4,110/25.4))
    fig.subplots_adjust(left=.025,right=.98,top=.84,bottom=.22,wspace=.10)
    fig.suptitle(title,fontsize=11,y=.967)
    bbox=g.total_bounds;pad=2000
    for i,(ax,p) in enumerate(zip(axs,panels)):
        source,col,cmap,lims,label=p
        g.plot(ax=ax,color='#E6E6E6',edgecolor='#C1C1C1',linewidth=.08)
        source.plot(ax=ax,column=col,cmap=cmap,vmin=lims[0],vmax=lims[1],edgecolor='none',missing_kwds={'color':'#CFCFCF'})
        # Original study polygons, not an invented service jurisdiction or county boundary.
        ax.set_xlim(bbox[0]-pad,bbox[2]+pad);ax.set_ylim(bbox[1]-pad,bbox[3]+pad);ax.set_aspect('equal');ax.set_anchor('N');ax.set_axis_off()
        ax.set_title(f'{chr(65+i)}  {label}',pad=6,fontsize=10)
        cb=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(*lims),cmap=cmap),ax=ax,orientation='horizontal',fraction=.037,pad=.028,aspect=25)
        cb.ax.tick_params(labelsize=8,length=2);cb.set_label('Geometry overlap (IoU)' if col=='canopy_land_geometry_IoU' else ('90% MOE (percentage points)' if '_moe90' in col else '%'),fontsize=8)
        x0=bbox[0]+.07*(bbox[2]-bbox[0]);y0=bbox[1]+.06*(bbox[3]-bbox[1])
        ax.plot([x0,x0+30000],[y0,y0],lw=1.5,color='#333333');ax.text(x0+15000,y0+3000,'30 km',ha='center',fontsize=8)
        ax.annotate('N',xy=(.95,.96),xytext=(.95,.86),xycoords='axes fraction',textcoords='axes fraction',ha='center',fontsize=8,arrowprops={'arrowstyle':'-|>','color':'#333333','lw':.8})
    footer(fig,note)
    export(pdf,fig,name,page)

def geographic(f):
    g=archived_boundaries().loc[f.index].join(f,rsuffix='_values')
    a=source_canopy().loc[f.index.intersection(source_canopy().index)].copy()
    a['canopy_percent']=100*f.canopy_2022_fraction.reindex(a.index)
    for c in CANDIDATES:
        g[c+'_percent']=100*g[c]
    for c in ['electric_heating_share','housing_5plus_share']:g[c+'_moe90_pp']=100*g[c+'_moe90']
    name='LIVING_ENVIRONMENT_GEOGRAPHIC_COVERAGE'
    with PdfPages(FOLDER/(name+'.pdf')) as pdf:
        map_pair(pdf,g,[(a,'canopy_percent','viridis',(0,50),'Published urban tree canopy'),(g,'canopy_land_geometry_IoU','cividis',(.75,1),'Source vs archived land geometry')],name,1,'Tree canopy and geographic support',
                 'Canopy uses its published polygons. IoU checks archived land masks; gray = unavailable/unresolved.\nExtent = frozen model-domain tracts, EPSG:3310. Urban-area greenness is not resident shade exposure.')
        map_pair(pdf,g,[(g,'parks_all_published_fraction_percent','viridis',(0,100),'Access to All Parks'),(g,'parks_good_published_fraction_percent','viridis',(0,100),'Access to Good Parks')],name,2,'Published park proximity: full 2,315-tract domain',
                 'Published percentages displayed by GEOID on frozen boundaries. Gray = undefined denominator.\nPopulation apportionment is unverified; geometric half-mile proximity is not pedestrian-network access.')
        map_pair(pdf,g,[(g,'electric_heating_share_percent','viridis',(0,100),'Electric principal heating'),(g,'housing_5plus_share_percent','viridis',(0,100),'Units in 5+ structures')],name,3,'ACS2018-2022 residential measurements',
                 'Heating denominator = occupied housing units; 5+ denominator = all housing units.\nGray = zero denominator. Maps locate tract aggregates; no resident locations or cluster labels inferred.')
        map_pair(pdf,g,[(g,'electric_heating_share_moe90_pp','magma',(0,20),'Heating uncertainty'),(g,'housing_5plus_share_moe90_pp','magma',(0,20),'Housing uncertainty')],name,4,'ACS ratio uncertainty: 80 official variance replicates',
                 '90% MOE in percentage points, including official boundary-variance rules. Color saturates above20.\nAll estimates retained. Exact MOEs and denominator flags are in ACS_UNCERTAINTY_AUDIT.csv.')

def redundancy(f):
    ref=f.loc[f.reference2287,CANDIDATES+CONTEXT]
    name='LIVING_ENVIRONMENT_REDUNDANCY'
    with PdfPages(FOLDER/(name+'.pdf')) as pdf:
        for page,method in enumerate(['pearson','spearman'],1):
            M=ref.corr(method=method);fig,ax=plt.subplots(figsize=(185/25.4,175/25.4))
            fig.subplots_adjust(left=.19,right=.93,top=.91,bottom=.25)
            im=ax.imshow(M,vmin=-1,vmax=1,cmap='RdBu_r')
            ax.set_xticks(range(8),['Canopy','All\nparks','Good\nparks','Heating','5+\nunits','EMC','log\ndensity','SOVI'],rotation=0,fontsize=8);ax.set_yticks(range(8),SHORT,fontsize=9)
            for t in ax.get_yticklabels():t.set_horizontalalignment('right')
            ax.tick_params(length=0,pad=5)
            for i in range(8):
                for j in range(8):ax.text(j,i,f'{M.iloc[i,j]:.2f}',ha='center',va='center',fontsize=9,color='white' if abs(M.iloc[i,j])>.6 else '#202020')
            ax.set_title(('Pearson correlation' if method=='pearson' else 'Spearman rank correlation')+' (N = 2,287)',fontsize=11,pad=14)
            cb=fig.colorbar(im,ax=ax,orientation='horizontal',fraction=.046,pad=.11,aspect=30);cb.ax.tick_params(labelsize=8)
            footer(fig,'Identical GEOIDs; unweighted tract associations, not causal effects.\nNested housing content and shared ACS sources require interpretation beyond correlation.\nParks definitions remain qualified even when marginal correlations are small.')
            export(pdf,fig,name,page)

def render():
    rows=[]
    for path in sorted(FOLDER.glob('*.pdf')):
        doc=fitz.open(path)
        for i,page in enumerate(doc):
            out=FOLDER/f'{path.stem}_native_page{i+1}.png';page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(out)
            fonts=[s['size'] for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
            rows.append(dict(file=path.name,page=i+1,width_mm=page.rect.width*25.4/72,height_mm=page.rect.height*25.4/72,min_text_pt=min(fonts),native_preview=out.name,high_resolution_dpi=600,visual_review='pending actual page inspection'))
        doc.close()
    save('FIGURE_RENDER_QA.csv',rows)
    log('Three diagnostic PDFs rendered at native185mm; every page exported at600dpi and native preview for visual inspection.')
if __name__=='__main__':
    f=pd.read_csv(lp(OUT/'LIVING_ENVIRONMENT_VALUES_2315.csv'),dtype={'tract_id':str},float_precision='round_trip').set_index('tract_id')
    distribution(f);geographic(f);redundancy(f);render()
