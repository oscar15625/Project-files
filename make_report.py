import run
import json,platform
from pathlib import Path
import numpy as np
import scipy,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

OUT=Path('output'); OUT.mkdir(exist_ok=True)
def get(tag): return json.loads((Path('results')/tag/'metrics.json').read_text())
b=get('sioux_node_theta1_without'); a=get('sioux_node_theta1_with'); w=get('sioux_wholesale_pt2')
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,2,figsize=(10,6.8),layout='constrained')
for ax,key,title,paper in zip(axs.flat,['share_drive','share_maas','profit_pt','profit_maas'],['Driving share (%)','MaaS share (%)','PT revenue ($)','MaaS profit ($)'],[[48.5,40.3],[0,39.5],[337286,375636],[0,5658]]):
    x=np.arange(2); ax.bar(x-.18,paper,.36,label='Paper',color='#17365d'); ax.bar(x+.18,[b[key],a[key]],.36,label='Reconstruction',color='#35a7a0'); ax.set_xticks(x,['Without','With']); ax.set_title(title); ax.ticklabel_format(axis='y',style='plain')
axs[0,0].legend(frameon=False); fig.suptitle('Sioux Falls: node-access alternative, theta = 1\nWholesale MoD = 1.5, PT = 1.0; not an exact reproduction',fontsize=13)
fig.savefig(OUT/'comparison.png',dpi=180); plt.close(fig)
cs=[.5,1,1.5,2,3]; rr=[get('sioux_wholesale_pt0.5'),a,get('sioux_wholesale_pt1.5'),w,get('sioux_wholesale_pt3')]
fig,axs=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
for k,label in [('profit_mod','MoD'),('profit_pt','PT'),('profit_maas','MaaS')]:
    axs[0].plot(cs,[r[k]/1000 for r in rr],'o-',label=label)
axs[0].axhline(b['profit_pt']/1000,color='gray',ls='--',label='PT without MaaS'); axs[0].axhline(b['profit_mod']/1000,color='gray',ls=':',label='MoD without MaaS'); axs[0].set(ylabel='Revenue / profit (thousand $)',xlabel='PT wholesale price'); axs[0].legend(fontsize=8)
axs[1].plot(cs,[(r['traveler_welfare']-b['traveler_welfare'])/abs(b['traveler_welfare'])*100 for r in rr],'o-',color='#35a7a0'); axs[1].set(xlabel='PT wholesale price',ylabel='Traveler welfare improvement (%)'); fig.suptitle('Sensitivity experiment: node-access alternative, MoD wholesale = 1.5')
fig.savefig(OUT/'sensitivity.png',dpi=180); plt.close(fig)

styles=getSampleStyleSheet(); styles['BodyText'].fontSize=10; styles['BodyText'].leading=14; styles['BodyText'].spaceAfter=8
story=[]
def p(text): story.append(Paragraph(text,styles['BodyText']))
def h(text): story.append(Paragraph(text,styles['Heading2']))
def table(rows,widths=None):
    t=Table(rows,colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17365d')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8.5),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),1,colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#edf2f7'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.extend([t,Spacer(1,10)])
story.append(Paragraph('MaaS multi-leader / multi-follower game',styles['Title']))
p('Independent reconstruction and verification report | 21 October 2026')
h('Finding: structural reconstruction, incomplete quantitative replication')
p('A runnable PUMCM-based multimodal equilibrium model has been implemented and tested on the small network and Sioux Falls. The implementation reproduces several qualitative mechanisms, but does not reproduce the published Tables 2 and 3 closely enough to claim numerical replication. The Korean companion report, REPRODUCTION.md, documents the full interpretation and remaining work.')
p('The most consequential unknowns are the experimental perturbation function/scale and the aggregation of service-access demand. Two access interpretations are retained: network-wide aggregate demand (literal reading of Section 5.1.1) and a node-based alternative. The latter is a deliberate alternative, not a recovered author setting.')
h('Verified qualitative result')
p('In the node-access alternative, a wholesale-price change can make both service operators, the MaaS platform and travelers better off. At the published PT wholesale price of 1.0, PT revenue falls instead. Thus the existence of a beneficial regime is reproduced, but not the paper\'s specific regime or its market shares.')
table([['Sioux Falls node alternative','Without','With c_PT=1','With c_PT=2'],['Driving share (%)',f'{b["share_drive"]:.2f}',f'{a["share_drive"]:.2f}',f'{w["share_drive"]:.2f}'],['MaaS share (%)','0',f'{a["share_maas"]:.2f}',f'{w["share_maas"]:.2f}'],['MoD revenue ($)',f'{b["profit_mod"]:,.0f}',f'{a["profit_mod"]:,.0f}',f'{w["profit_mod"]:,.0f}'],['PT revenue ($)',f'{b["profit_pt"]:,.0f}',f'{a["profit_pt"]:,.0f}',f'{w["profit_pt"]:,.0f}'],['MaaS profit ($)','0',f'{a["profit_maas"]:,.0f}',f'{w["profit_maas"]:,.0f}']],[190,85,105,105])
p('The source paper is Yao, Ma and Zhang (2026), Transportation Research Part C 188, 105703, DOI 10.1016/j.trc.2026.105703. Equations were extracted from the supplied published PDF. The supplied PUMCM reference is a four-page TRISTAN XII extended abstract, not a complete implementation specification.')
story.append(PageBreak())
h('1. Model and computational method')
p('Utilities follow Eqs. (4)-(6): MaaS passengers pay an OD fare at entry; non-MaaS passengers pay per-distance MoD fares or per-link PT fares; driving has a fixed entry cost and a distance cost. Separate MaaS, non-MaaS and driving state spaces prevent mid-trip switching between the three categories. Transfers between services remain possible inside each service category.')
p('We specialize PUMCM to negative Shannon entropy with scale theta=1 and discount=1, following the simulation choice in the supplied reference abstract. For W_ij=exp(-cost_ij/theta) and z_i=exp(V_i/theta), the Bellman fixed point is (I-W)z=b, with terminal weights b. Transition probabilities are W_ij z_j/z_i. Transpose sparse solves produce expected link flows. This is an exact fixed-point solver for this specialization, not shortest-path or enumerated-route assignment.')
p('Implicit differentiation of the same linear systems produces retail-price derivatives of values, path revenues and market shares. The traffic block balances shared road/access demand with inverse-BPR supply and PT capacities. The service blocks use own-profit partial derivatives while holding other leaders\' variables fixed, as in Eqs. (18) and (20).')
p('For an OD MaaS fare, expected conditional wholesale cost C is independent of that entry fare. The first-order condition is p-C=theta/(1-s), where s is the MaaS share. A Lambert W expression solves this condition exactly and removes weakly identified high-fare variables from the numerical root solve.')
h('Algorithm fidelity')
p('run.py implements the two-evaluation extragradient iteration (24)-(25). A direct small-network run with the published step 1e-4 did not converge: the natural residual oscillated near 0.02. Final results use a documented auxiliary root solver for the same constructed VI. Congestible times are represented by flow/capacity ratios to avoid cancellation at free flow. These runs do not reproduce the paper\'s iteration count or convergence curve.')
h('Input parameters')
table([['Parameter','Small','Sioux Falls'],['Demand','1,000; 3 OD pairs','432,720; 528 positive OD pairs'],['Road network','8 nodes; 12 directed links','24 nodes; 76 directed links'],['BPR alpha, beta','0.15, 4','0.15, 4'],['MoD access time / capacity','1 / 100','1 / 60,000'],['PT access time / capacity','2 / 500','2 / 30,000'],['Fixed driving / distance cost','5 / 0.2','2 / 0.2'],['Transfer penalty non / MaaS','10 / 1 or 3','8 / 0.5'],['Wholesale MoD / PT','1.3 / 1.3','1.5 / 1.0']],[195,135,155])
story.append(PageBreak())
h('2. Comparison with the published Sioux Falls experiment')
story.append(Image(str(OUT/'comparison.png'),width=7*inch,height=4.76*inch))
p('The node-access alternative improves traveler welfare by 13.55%, compared with the paper\'s 14.0%, and reduces driving by 2.77 percentage points, compared with 8.2. However, MaaS share is 17.23% instead of 39.5%, PT revenue declines instead of increasing, and MaaS profit is much larger. The agreement in traveler welfare does not validate the unmatched components.')
p('Under the aggregate-access interpretation, the no-MaaS driving share is 69.25%, far from the paper\'s 48.5%. Both interpretations are retained; the more favorable comparison is not presented as the definitive author model.')
p('All transfer links are counted in the reconstruction\'s transfer_flow output. The paper\'s reported transfer-flow aggregation and units were not recovered. Detailed MoD/PT share subcategories are also not asserted equivalent; OD-level shares of MaaS, non-MaaS and driving are exported unambiguously.')
story.append(PageBreak())
h('3. Wholesale and transfer sensitivity')
story.append(Image(str(OUT/'sensitivity.png'),width=7*inch,height=2.66*inch))
p('At c_PT=2, with c_MoD fixed at 1.5, MoD revenue rises by 16.70% and PT revenue by 17.00% relative to the node-access no-MaaS baseline. MaaS earns 94,514 and traveler welfare improves by 9.27%. These are reconstructed outcomes under an altered wholesale price, not the published baseline.')
p('Only five PT wholesale prices were tested. The experiment establishes favorable sampled points, not an analytically certified continuous Pareto-improving interval. A sensitivity script reproduces these cases from a common warm start.')
h('Small network')
s0=get('small_node_theta1_without'); s1=get('small_node_theta1_with'); s3=get('small_node_moderate')
table([['Node-access case','Without','Penalty 1','Penalty 3'],['Driving share (%)',f'{s0["share_drive"]:.2f}',f'{s1["share_drive"]:.2f}',f'{s3["share_drive"]:.2f}'],['MaaS share (%)','0',f'{s1["share_maas"]:.2f}',f'{s3["share_maas"]:.2f}'],['MaaS profit ($)','0',f'{s1["profit_maas"]:.2f}',f'{s3["profit_maas"]:.2f}'],['Transfer flow',f'{s0["transfer_flow"]:.2f}',f'{s1["transfer_flow"]:.2f}',f'{s3["transfer_flow"]:.2f}']],[200,90,95,100])
p('Both small-network service operators and travelers benefit in the penalty-1 node alternative. Raising the transfer penalty to 3 reduces MaaS adoption and transfers, matching the paper\'s qualitative mechanism. Absolute revenues and mode shares still differ. Theta=2 runs are retained as sensitivity tests, not parameter estimates.')
story.append(PageBreak())
h('4. Numerical verification and excluded solutions')
p('An independent two-route example matches closed-form logit values, probabilities and flows. Finite-difference checks of the two operator profit gradients and one OD MaaS gradient on both networks have maximum relative error about 1.1e-9. Terminal-flow conservation errors in the main final runs are at most 1.1e-11. Shares sum to 100%.')
p('The four node-access baseline scenarios satisfy the paper\'s natural projected residual tolerance of 1e-6. A unilateral retail-price grid over [0,10], plus checks at 20, 50, 100 and 200, with bounded local refinement, finds no material profitable deviations. The test holds traffic times and other prices fixed. It is a numerical check, not a global mathematical certificate.')
p('An early aggregate-access Sioux Falls run converged numerically at PT price 200 but failed the deviation test: PT could gain 56,716.90 by changing its price. It is explicitly excluded. A corrected aggregate solution is saved separately. Historical files with small residuals must not automatically be treated as valid strategic equilibria; consult audit.json and the report.')
h('Why missing behavior parameters matter')
p('For this Shannon specialization, every interior optimal MaaS OD fare satisfies profit_OD = theta * demand_OD/(1-share_OD), hence total MaaS profit is at least theta times total MaaS demand. The paper\'s Sioux Falls share 39.5% and demand 432,720 imply demand about 170,924, but reported MaaS profit is 5,658. Therefore unit-scale Shannon behavior with the reconstructed accounting cannot reproduce both numbers. This identifies a missing specification or accounting difference; it is not evidence that the general PUMCM paper is wrong.')
h('Unresolved details')
p('Needed for faithful numerical replication: the actual perturbation function and state-dependent scales; exact access-demand aggregation; dummy-link and destination construction; small-network PT connectivity/capacities; wholesale units; share and transfer definitions; initialization and upper bounds. The small-network prose/figure and Appendix A.1 are not fully consistent about PT nodes, so Appendix A.1 was prioritized. Small PT physical capacity 1,000,000 is an assumption; Sioux Falls specifies that value.')
p('Not reproduced: all published figures, the original initial-state robustness exercise, VOT and selected-link-capacity sensitivity experiments, or the original fixed-step convergence trajectory. No author contact was sent.')
story.append(PageBreak())
h('5. Reproducible artifacts and version history')
p('The workspace contains source code, raw TNTP inputs, explicit assumptions, validation scripts, saved solver states, run metrics, OD-level fares/shares/values and resource-level flows/times. data/provenance.json records source blob IDs and SHA-256 hashes. results/final_manifest.json identifies the selected comparison runs. Failed and superseded experiments remain as research history.')
table([['File','Purpose'],['src/model.py','Network, PUMCM, flow loading, sensitivities, VI'],['run.py / refine.py','Extragradient / equivalent-VI root refinement'],['validate.py / audit.py','Independent loading, derivative and deviation checks'],['experiments.py / sensitivity.py','Scenario pairs and wholesale/transfer experiments'],['export_results.py','OD and resource CSV exports, source provenance'],['REPRODUCTION.md','Detailed Korean report and reproduction limits'],['output/comparison.png / sensitivity.png','Publication comparison and sensitivity charts']],[205,280])
p('Install requirements.txt with Python 3.12. Run validate.py, then experiments.py with --network small or sioux and --access aggregate or node. Run sensitivity.py, audit.py, export_results.py and make_report.py. The workspace automatically uses .vendor when present; a regular Python environment also works.')
p('GitHub branch: <link href="https://github.com/oscar15625/Project-files/tree/maas-reproduction-2026-10-21">oscar15625/Project-files / maas-reproduction-2026-10-21</link>. Local Git bundles preserve milestone versions. The supplied paper PDFs are not published to GitHub.')
h('Sources')
p('Yao, R., Ma, X., Zhang, K. (2026). Mobility-as-a-service (MaaS) system as a multi-leader-multi-follower game: A single-level variational inequality (VI) formulation. TRC 188, 105703. DOI: 10.1016/j.trc.2026.105703. Supplied published PDF, equations 1-28, Tables 1-3 and Appendix A.')
p('Yao, R., Zhang, K. (2025). Perturbed utility Markovian choice model: choice probability generation function and estimation. Supplied TRISTAN XII extended abstract, especially its simulation specification.')
p('Transportation Networks for Research: github.com/bstabler/TransportationNetworks/tree/master/SiouxFalls, downloaded 21 October 2026. HOMES publication listing: epfl.ch/labs/homes/publications/. Public-code searches did not identify the authors\' implementation; this is not a proof of absence.')
def footer(canvas,doc):
    canvas.setFont('Helvetica',8); canvas.setFillColor(colors.gray); canvas.drawString(42,26,'MaaS reconstruction | Assumptions and non-replication limits are explicit'); canvas.drawRightString(565,26,str(doc.page))
SimpleDocTemplate(str(OUT/'MaaS_reproduction_report.pdf'),pagesize=(612,792),rightMargin=42,leftMargin=42,topMargin=36,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
Path('environment.json').write_text(json.dumps({'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'platform':platform.platform()},indent=2))
print('Created report and plots.')
