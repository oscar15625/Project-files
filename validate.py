import run
import numpy as np
import json
from pathlib import Path
from src.model import Model

def validate():
    report={}
    for name in ['small','sioux']:
        m=Model(name,True); y=m.initial(); h,metrics=m.evaluate(y)
        errs=[]
        for idx,key in [(-2,'profit_mod'),(-1,'profit_pt'),(m.nt,'profit_maas')]:
            eps=1e-5; a=y.copy(); b=y.copy(); a[idx]+=eps; b[idx]-=eps
            fd=(m.evaluate(a)[1][key]-m.evaluate(b)[1][key])/(2*eps)
            errs.append(abs(fd+h[idx])/max(1,abs(fd)))
        assert max(errs)<1e-6,(name,errs)
        assert metrics['flow_conservation_error']<1e-7,metrics
        assert abs(sum(metrics[k] for k in ['share_non','share_drive','share_maas'])-100)<1e-10
        report[name]={'gradient_relative_errors':errs,'flow_conservation_error':metrics['flow_conservation_error'],'demand':m.total,'road_links':len(m.rows),'od_pairs':m.nod}
    Path('results/validation.json').write_text(json.dumps(report,indent=2,default=float)); print(report)
if __name__=='__main__': validate()
