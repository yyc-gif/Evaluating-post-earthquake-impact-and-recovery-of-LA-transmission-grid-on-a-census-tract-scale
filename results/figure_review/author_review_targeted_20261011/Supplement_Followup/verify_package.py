"""Record exact preservation and verified review-package delivery hashes."""
from pathlib import Path
import sys,json,hashlib,csv,datetime,os,xml.etree.ElementTree as ET
os.environ['GIT_OPTIONAL_LOCKS']='0'
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import common as c
P=Path(__file__).resolve().parent;c.PKG=P

def preservation():
    with open(c.lp(P.parent/'PRESERVATION_BEFORE.json'),encoding='utf-8') as f:old=json.load(f)
    current={'original_HEAD':c.git('rev-parse','HEAD',root=c.ORIGINAL).decode().strip(),
       'protected_files':{p:c.sha(c.ORIGINAL/p) for p in old['protected_files']},
       'protected_count':len(old['protected_files']),
       'index_sha256':hashlib.sha256(c.git('ls-files','--stage','-z',root=c.ORIGINAL)).hexdigest(),
       'status_sha256':hashlib.sha256(c.git('status','--porcelain=v1','-z',root=c.ORIGINAL)).hexdigest(),
       'staged_count':len([p for p in c.git('diff','--cached','--name-only','-z',root=c.ORIGINAL).split(b'\0') if p])}
    assert current==old,'Original scientific files or working-tree/index state changed'
    c.dump('PRESERVATION_VERIFICATION.json',current)
    return current

if __name__=='__main__':
    protected=preservation()
    with open(c.lp(P.parent/'OUTPUT_HASHES.json'),encoding='utf-8') as f:previous=json.load(f)
    assert all(c.sha(P.parent/rel)==r['sha256'] for rel,r in previous.items())
    tests=ET.parse(c.lp(P/'TEST_RESULTS.xml')).getroot().find('testsuite')
    assert int(tests.attrib['tests'])==7 and int(tests.attrib['failures'])==0 and int(tests.attrib['errors'])==0
    with open(c.lp(P/'ARTWORK_EDIT_RECORDS.json'),encoding='utf-8') as f:records=json.load(f)
    with open(c.lp(P/'CANDIDATE_MANIFEST.csv'),'w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['figure','candidate_file','sha256','png_sha256','width_mm','height_mm','min_font_pt','status'])
        writer.writeheader()
        for name,r in records.items():writer.writerow({'figure':name,'candidate_file':r['file'],'sha256':r['sha256'],
          'png_sha256':c.sha(P/(name+'_Candidate.png')),'width_mm':r['size_mm'][0],'height_mm':r['size_mm'][1],
          'min_font_pt':r['min_font_pt'],'status':'AUTHOR_REVIEW_ONLY — NOT PROMOTED'})
    c.dump('NUMERICAL_INVARIANCE_QA.json',{'tests_passed':7,'formal_outputs_modified':False,'new_scientific_evaluations':0,
       'original_protected_files_unchanged':protected['protected_count'],'original_staged_items_unchanged':protected['staged_count'],
       'previous_review_package_hashes_unchanged':True,'source_hashes_verified':'SOURCE_HASHES.json',
       'verification':'Exact saved curve/cell values; unchanged map paths and retained matrix pixels; source registration; native widths and caption completeness.'})
    exclusions={'OUTPUT_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json'}
    manifest={}
    for f in sorted(P.rglob('*')):
        if not f.is_file() or f.name in exclusions:continue
        rel=f.relative_to(P).as_posix()
        import subprocess
        result=subprocess.run(['git','-C',str(c.ROOT),'check-ignore','--quiet',str(f)],capture_output=True)
        if result.returncode==0:continue
        manifest[rel]={'sha256':c.sha(f),'bytes':f.stat().st_size}
    c.dump('OUTPUT_HASHES.json',manifest)
    print('Verified',len(manifest),'delivery files;',protected['protected_count'],'protected files;',protected['staged_count'],'staged items intact.')
