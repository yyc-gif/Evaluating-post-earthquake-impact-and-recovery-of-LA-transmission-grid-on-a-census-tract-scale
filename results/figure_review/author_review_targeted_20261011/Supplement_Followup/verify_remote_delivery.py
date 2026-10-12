"""Check this supplement package using actual downloaded remote LFS bytes."""
from pathlib import Path
import sys,runpy
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import common
common.PKG=Path(__file__).resolve().parent
runpy.run_path(str(common.PKG.parent/'verify_remote_delivery.py'),run_name='__main__')
