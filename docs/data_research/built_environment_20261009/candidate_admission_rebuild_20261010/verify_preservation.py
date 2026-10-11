from common import *
import pandas as pd,collections

if __name__=='__main__':
 current=snapshot();before=json.loads((OUT/'PRESERVATION_BEFORE.json').read_text());dump('PRESERVATION_AFTER.json',current)
 changed=[k for k in before['protected_files'] if before['protected_files'][k]!=current['protected_files'][k]]
 for key in ['original_head','original_branch','logical_index_sha256','status_sha256','staged_count']:
  assert before[key]==current[key],f'Original worktree changed: {key}'
 assert not changed,'Protected-file changes: '+str(changed)
 inventory={}
 for directory in ['Data','Formal_Experiment_20260923','src','config','results']:
  for p in (ORIGINAL/directory).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
    rel=p.relative_to(ORIGINAL).as_posix();stat=p.stat()
    hash_extra=directory in ['Data','src','config'] or (directory=='Formal_Experiment_20260923' and len(p.relative_to(ORIGINAL).parts)<=3 and p.suffix in ['.csv','.npz','.parquet'])
    h=current['protected_files'][rel]['sha256'] if rel in current['protected_files'] else (sha(p) if hash_extra else None)
    inventory[rel]={'sha256':h or '', 'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'verification':'start_manifest_byte_hash' if rel in current['protected_files'] else ('additional_input_byte_hash' if h else 'additional_event_review_diagnostic_inventory_only')}
  log(f'Current inventory complete for {directory}; total entries={len(inventory)}')
 target=OUT/'CURRENT_PROTECTION_INVENTORY.json'
 frame=pd.DataFrame.from_dict(inventory,orient='index').rename_axis('file').reset_index();manifest=OUT/'CURRENT_PROTECTION_INVENTORY.csv'
 if manifest.exists():
  old=pd.read_csv(manifest,keep_default_na=False);pd.testing.assert_frame_equal(frame,old,check_dtype=False)
 else:frame.to_csv(manifest,index=False)
 dump('CURRENT_PROTECTION_INVENTORY.json',{'scope':'all existing Data, Formal_Experiment, src, config, results files excluding pycache; full current path/size/mtime census, start-manifest plus additional input byte hashes','manifest':'CURRENT_PROTECTION_INVENTORY.csv','manifest_sha256':sha(manifest),'count':len(inventory),'counts_by_directory':dict(collections.Counter(k.split('/')[0] for k in inventory)),'byte_hashed_count':int(frame.sha256.ne('').sum()),'timing':'current census before publication; start-of-task950-file hashes separately verified; no retrospective byte-hash claim for newly inventoried tiny events and diagnostic archives'})
 dump('PROTECTED_SOURCE_VERIFICATION.json',{'start_snapshot_protected_files':current['protected_count'],'current_expanded_inventory_files':len(inventory),'staged_items_before':before['staged_count'],'staged_items_after':current['staged_count'],'original_index_unchanged':True,'original_status_unchanged':True,'scientific_files_changed_in_start_manifest':len(changed),'new_clustering_fits':0,'new_simulation_GA_scheduling_runs':0})
 log(f'Preservation confirmed: {current["protected_count"]} files, {current["staged_count"]} staged items; scientific files changed=0')
