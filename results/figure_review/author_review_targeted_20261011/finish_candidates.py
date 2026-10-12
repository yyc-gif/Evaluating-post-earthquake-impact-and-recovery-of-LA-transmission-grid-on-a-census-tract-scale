from common import *
from revise_artwork import framework,load_geography,overlay_quartiles,INPUTS
import shutil
records=json.load(open(lp(PKG/'ARTWORK_EDIT_RECORDS.json'),encoding='utf-8'))
d,info=framework();records['Fig01']=dict(export(d,'Fig01_Author_Review'),edits=info)
geo,audit=load_geography();d=overlay_quartiles(geo,dissolve=True)
records['Fig05_recommended']=dict(export(d,'Fig05_Q4_Context_Candidate'),
    overlay='outer boundaries of the exact Q4 polygon union; adjoining Q4 internal edges omitted',
    width_pt=.24,alpha=.75)
for ext in ['.pdf','.png']:
    shutil.copyfile(lp(PKG/('alternatives/Fig07_Color_B'+ext)),lp(PKG/('Fig07_Cluster_Color_Candidate'+ext)))
records['Fig07_recommended']=dict(records['Fig07_B'],file='Fig07_Cluster_Color_Candidate.pdf')
old=json.load(open(lp(PKG/'SOURCE_HASHES.json'),encoding='utf-8'));old.update(INPUTS)
dump('SOURCE_HASHES.json',old);dump('ARTWORK_EDIT_RECORDS.json',records)
print('Recommended candidates ready',flush=True)
