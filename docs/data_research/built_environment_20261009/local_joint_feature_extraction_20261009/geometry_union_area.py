"""Exact polygon-union area by disjoint overlap components (no double counting)."""
import numpy as np,shapely
class UnionArea:
 def __init__(self,geometries):
  self.gs=geometries;self.ids={id(g):i for i,g in enumerate(geometries)};self.areas=np.asarray([g.area for g in geometries]);self.parent=list(range(len(geometries)));self.memo={}
  if len(geometries):
   a=np.asarray(geometries,dtype=object);pairs=shapely.STRtree(a).query(a,predicate='intersects');m=pairs[0]<pairs[1];ii,jj=pairs[:,m]
   if len(ii):
    positive=shapely.area(shapely.intersection(a[ii],a[jj]))>0
    for i,j in zip(ii[positive],jj[positive]):self.parent[self.root(int(j))]=self.root(int(i))
  self.component={i:self.root(i) for i in range(len(geometries))}
 def root(self,i):
  while self.parent[i]!=i:self.parent[i]=self.parent[self.parent[i]];i=self.parent[i]
  return i
 def area(self,subset):
  key=tuple(sorted(self.ids[id(g)] for g in subset))
  if key in self.memo:return self.memo[key]
  groups={}
  for i in key:groups.setdefault(self.component[i],[]).append(i)
  total=0.
  for ids in groups.values():
   if len(ids)==1:total+=self.areas[ids[0]]
   else:total+=shapely.union_all([self.gs[i] for i in ids]).area
  self.memo[key]=float(total);return float(total)
