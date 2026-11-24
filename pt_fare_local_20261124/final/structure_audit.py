from extension import *
from scipy.sparse.csgraph import shortest_path
os.chdir(ROOT)
rows,lines,ods=inputs('sioux');stations=set(n for line in lines for n in line);adj=np.zeros((25,25))
for line in lines:
 for a,b in zip(line[:-1],line[1:]):adj[a,b]=adj[b,a]=1
hops=shortest_path(adj,directed=False,unweighted=True)
eligible=[(int(o),int(d),q,hops[int(o),int(d)]) for o,d,q in ods if o in stations and d in stations]
record=dict(road_nodes=24,directional_road_links=len(rows),PT_lines=lines,PT_nodes=len(stations),unique_undirected_PT_links=int(adj.sum()/2),positive_OD=len(ods),total_demand=sum(o[2] for o in ods),station_endpoint_OD=len(eligible),station_endpoint_demand=sum(r[2] for r in eligible),minimum_PT_hops=min(r[3] for r in eligible),maximum_PT_hops=max(r[3] for r in eligible),weighted_PT_hops=sum(r[2]*r[3] for r in eligible)/sum(r[2] for r in eligible))
assert record['positive_OD']==528 and record['total_demand']==432720 and record['station_endpoint_OD']==174 and record['station_endpoint_demand']==164040
checks=[]
for maas in [False,True]:
 m=make('sioux','link',maas)
 for _,gr in m.graphs:
  g=gr['non']
  for (s,j),a in zip(g.edge_labels,g.attr):
   ride=isinstance(s[0],int) and isinstance(j[0],int) and s[0]==j[0] and s[1]!=j[1]
   assert a[3]==int(ride)
   if s[0]=='M' and j[0]=='M':assert abs(a[2]-next(r[2] for r in rows if r[:2]==(s[1],j[1])))<1e-12
 checks.append(dict(maas=maas,Eq27_link_tariff='PASS',MoD_distance_tariff='PASS'))
write(ROOT/'audit/sioux_structure.json',dict(status='PASS',structure=record,Eq27_checks=checks,caveat='Shortest PT-only paths, not equilibrium routing; fixed input at b682637. Physical MoD access is aggregate, PT access node-specific.'))
print(json.dumps(record,indent=2))
