"""Render one saved native PDF in a fresh process, with no source computation."""
import sys
from pathlib import Path
import fitz

def lp(p):
    s=str(Path(p).resolve())
    return s if s.startswith('\\\\?\\') else '\\\\?\\'+s

if __name__=='__main__':
    doc=fitz.open(lp(sys.argv[1]));assert len(doc)==1
    for dpi,path in [(600,sys.argv[2]),(160,sys.argv[3])]:
        pix=doc[0].get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False)
        pix.set_dpi(dpi,dpi);pix.save(lp(path))
