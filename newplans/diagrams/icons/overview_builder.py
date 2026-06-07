#!/usr/bin/env python3
"""Hand-laid swimlane overview (hall-of-fame style). Emits .drawio (editable) + .png preview.
Medallion = storage layers (MinIO/Iceberg) with Spark as the transform between them.
Sources split into batch / stream / cdc."""
import base64, os, html, cairosvg

IC = "/tmp/icons/png"
OUTDIR = "/mnt/data/mlops/Long-project/face-detect-gke/plans/260604-2213-mlops-l2-l3-rag-complete-build/diagrams/icons"
W, H = 2320, 1420

# ---- swimlane zones ----
ZONES = [
 (24,  60, 2272,118, "Platform  ·  IaC + CI/CD (GitOps) + SSO + Mesh + Policy",       "#eef2f7", "#9aa4b2"),
 (24, 192, 2272,360, "Data Pipeline (L2)  ·  Iceberg Lakehouse  (batch + stream + CDC)","#e9f3fe","#7badd6"),
 (24, 566, 2272,176, "Training Pipeline (L3)",                                  "#eef7ee", "#86bf86"),
 (24, 756, 2272,150, "Serving Pipeline (L3)",                                   "#fff3e6", "#e0a86a"),
 (24, 920, 2272,156, "Drift -> Retrain -> Canary Loop  *  (L3 centerpiece)",    "#fdecec", "#d98a8a"),
 (24,1090, 2272,150, "RAG / LLM (L3 · AI Track 4B)",                            "#f3eefb", "#b193d6"),
 (24,1254, 2272,140, "Observability",                                          "#eafaf0", "#86c9a8"),
]

N = {}
def ni(id,x,y,icon,label): N[id]=(x,y,'i',icon,label)
def na(id,x,y,fill,label): N[id]=(x,y,'a',fill,label)

# ---------------- Platform (row y=120) : IaC + CI + CD + SSO + mesh + policy ----------------
na("dev",      95,120,"#dfe7f0","Developer")
ni("github",   225,120,"github","GitHub")
ni("gha",      360,120,"githubactions","GitHub Actions\nbuild+test")
ni("fdimage",  490,120,"fdimage","face-detect\nimage")
ni("registry", 615,120,"docker","Image registry")
ni("argocd",   745,120,"argocd","ArgoCD\nCD (GitOps)")
ni("terraform",880,120,"terraform","Terraform\nGKE+GPU")
ni("ansible", 1010,120,"ansible","Ansible")
ni("keycloak",1170,120,"keycloak","Keycloak SSO")
ni("istio",   1320,120,"istio","Istio ambient")
ni("vault",   1460,120,"vault","Vault + ESO")
ni("kyverno", 1590,120,"kyverno","Kyverno")
ni("certmgr", 1710,120,"certmanager","cert-manager")

# ---------------- Data (y 200..548) ----------------
# sources (3 sub-rows, left)
na("wider", 110,300,"#cfe0f3","WIDER FACE\n(batch)")
na("camera",110,400,"#cfe0f3","Camera / API\n(stream)")
na("appdb", 110,490,"#cfe0f3","App DB\n(CDC)")
# ingestion
ni("debezium",280,490,"debezium","Debezium")
ni("kafka",  300,400,"kafka","Kafka topics")
ni("schemareg",380,490,"schemaregistry","Schema Registry")
ni("flink",  470,400,"flink","Flink validate")
ni("redis",  570,490,"redis","Feast online")
# medallion: STORAGE layers with SPARK transforms between
ni("minio_b",470,300,"minio","MinIO\nBronze (S3)")
ni("spark1", 650,300,"spark","Spark\ntransform")
ni("ge1",    650,225,"greatexpectations","GE #1")
ni("minio_s",830,300,"minio","MinIO\nSilver (S3)")
ni("spark2",1010,300,"spark","Spark\ntransform")
ni("ge2",   1010,225,"greatexpectations","GE #2")
ni("gold", 1190,300,"iceberg","Iceberg\nGold")
# storage / query / catalog (right)
ni("lakefs",1010,430,"lakefs","lakeFS\n(versioning)")
ni("trino", 1190,430,"trino","Trino")
ni("pg",    1380,430,"postgresql","PostgreSQL DW")
ni("airflow",650,470,"airflow","Airflow")
ni("openmeta",1380,300,"openmetadata","OpenMetadata\ncatalog+RBAC")

# ---------------- Training (y=640) ----------------
ni("notebooks",470,628,"kubeflow","Notebooks")
ni("feast",   660,640,"feast","Feast offline")
ni("kubeflow",850,640,"kubeflow","Kubeflow\nPipelines")
ni("katib",  1040,610,"katib","Katib HPO")
ni("ray",    1040,672,"ray","Ray train\nGPU / CPU")
ni("mlflow", 1230,640,"mlflow","MLflow\nregistry")
ni("onnx",   1420,640,"nvidia","ONNX(CPU)/TensorRT(GPU)")

# ---------------- Serving (y=830) ----------------
na("enduser",110,830,"#f2dcc2","End User")
ni("kserve", 330,830,"kserve","KServe")
ni("triton", 510,830,"nvidia","Triton (GPU/CPU)")
ni("keda",   700,800,"keda","KEDA")
ni("flagger",700,862,"flagger","Flagger canary")

# ---------------- Drift (y=998) ----------------
ni("evidently",330,998,"evidently","Evidently")
ni("alibi",   520,998,"alibidetect","Alibi Detect")
ni("prom",    720,998,"prometheus","Prometheus")
ni("alertmgr",910,998,"alertmanager","Alertmanager")
ni("argoev", 1100,998,"argo","Argo Events")

# ---------------- RAG (y=1165) ----------------
na("question",110,1165,"#e6dcf3","User question")
ni("ragflow", 320,1165,"ragflow","RAGFlow")
ni("qdrant",  500,1135,"qdrant","Qdrant")
ni("typesense",500,1198,"typesense","Typesense")
ni("guardrails",690,1165,"guardrails","Guardrails")
ni("vllm",    870,1165,"vllm","vLLM / Ollama")
ni("langfuse",1050,1165,"langfuse","Langfuse")

# ---------------- Observability (y=1322) ----------------
ni("thanos", 330,1322,"thanos","Thanos")
ni("grafana",510,1322,"grafana","Grafana")
ni("elk",    700,1322,"elasticsearch","ELK")
ni("kibana", 880,1322,"elasticsearch","Kibana")
ni("jaeger",1070,1322,"jaeger","Jaeger + OTel")

# ---- edges: (src,dst,label,color,dashed) ----
E = [
 ("dev","github","code","#5b6472",0),("github","gha","push","#5b6472",0),("gha","fdimage","build","#5b6472",0),("fdimage","registry","push image","#5b6472",0),("registry","argocd","image","#5b6472",0),("argocd","kserve","deploy app","#5b6472",1),("terraform","ansible","then","#9aa4b2",1),("ansible","istio","provision GKE+GPU","#9aa4b2",1),
 # data — split flows
 ("wider","minio_b","(1b) batch","#1864ab",0),
 ("camera","kafka","(1s) stream","#1864ab",0),
 ("appdb","debezium","cdc","#1864ab",0),("debezium","kafka","","#1864ab",0),
 ("schemareg","kafka","schema","#9aa4b2",1),
 ("kafka","flink","(2) validate","#1864ab",0),
 ("flink","redis","online feat","#1864ab",1),("flink","minio_b","valid","#1864ab",1),
 # medallion: storage --Spark--> storage
 ("minio_b","spark1","(3) read","#1864ab",0),("spark1","minio_s","write","#1864ab",0),
 ("ge1","minio_s","check","#2b8a3e",1),
 ("minio_s","spark2","read","#1864ab",0),("spark2","gold","(4) write Gold","#1864ab",0),
 ("ge2","gold","check","#2b8a3e",1),
 ("gold","lakefs","version","#9aa4b2",1),("trino","gold","SQL","#1864ab",0),
 ("gold","pg","DW","#1864ab",0),("airflow","spark1","schedule","#9aa4b2",1),
 ("gold","openmeta","lineage","#2b8a3e",1),
 # training
 ("trino","feast","(5) load","#2b8a3e",0),("feast","kubeflow","features","#2b8a3e",0),
 ("notebooks","kubeflow","author","#9aa4b2",1),("kubeflow","katib","HPO","#2b8a3e",0),
 ("kubeflow","ray","train","#2b8a3e",0),("kubeflow","mlflow","(6) register","#2b8a3e",0),
 ("mlflow","onnx","export","#2b8a3e",0),
 # serving
 ("enduser","kserve","(7) request","#b8741a",0),("mlflow","kserve","deploy","#b8741a",1),
 ("kserve","triton","runtime","#b8741a",0),("redis","kserve","features","#b8741a",1),
 ("keda","kserve","scale","#9aa4b2",1),("flagger","kserve","(10) promote","#c92a2a",1),
 # drift
 ("kserve","evidently","(8) predictions","#c92a2a",0),("kserve","alibi","inputs","#c92a2a",1),
 ("evidently","prom","drift_score","#c92a2a",0),("prom","alertmgr","alert","#c92a2a",0),
 ("alertmgr","argoev","webhook","#c92a2a",0),("argoev","kubeflow","(9) retrain","#c92a2a",1),
 # rag
 ("question","ragflow","ask","#7c3aed",0),("ragflow","qdrant","vector","#7c3aed",0),
 ("ragflow","typesense","keyword","#7c3aed",0),("qdrant","guardrails","context","#7c3aed",0),
 ("guardrails","vllm","generate","#7c3aed",0),("vllm","langfuse","trace","#7c3aed",1),
 ("openmeta","qdrant","index","#9aa4b2",1),
 # observability
 ("prom","thanos","store","#059669",0),("thanos","grafana","viz","#059669",0),
 ("elk","kibana","view","#059669",0),("kserve","elk","logs","#059669",1),("kserve","jaeger","traces","#059669",1),
]


KEEP={"(1b) batch","(1s) stream","cdc","(2) validate","(3) read","(4) write Gold","(5) load",
 "(6) register","(7) request","(8) predictions","(9) retrain","(10) promote","drift_score",
 "alert","webhook","vector","keyword","generate","code","push","build","push image","deploy app","provision GKE+GPU"}
E=[(a,b,(l if l in KEEP else ""),c,d) for a,b,l,c,d in E]

IW, IH = 56, 56
AW, AH = 124, 54
def _b64(p): return base64.b64encode(open(p,"rb").read()).decode()

def anchors(id):
    x,y,k,_,_=N[id]; w=IW if k=='i' else AW; h=IH if k=='i' else AH
    return dict(x=x,y=y,l=(x-w/2,y),r=(x+w/2,y),t=(x,y-h/2),b=(x,y+h/2),w=w,h=h)

def route(s,d):
    a,b=anchors(s),anchors(d); dx=b['x']-a['x']; dy=b['y']-a['y']
    if abs(dy)<24:
        p=[a['r'],b['l']] if dx>=0 else [a['l'],b['r']]
        mx=(p[0][0]+p[1][0])/2; return [p[0],(mx,p[0][1]),(mx,p[1][1]),p[1]]
    start=a['b'] if dy>0 else a['t']; end=b['t'] if dy>0 else b['b']
    midy=(start[1]+end[1])/2
    return [start,(start[0],midy),(end[0],midy),end]

def ZONE_AT(yy):
    for x,y,w,h,t,fill,st in ZONES:
        if y<=yy<=y+h: return fill
    return "#ffffff"

def svg():
    L=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'viewBox="0 0 {W} {H}" font-family="DejaVu Sans, Arial, sans-serif">',
       f'<rect width="{W}" height="{H}" fill="#ffffff"/>','<defs>']
    for c in set(e[3] for e in E):
        L.append(f'<marker id="m{c.replace("#","")}" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="{c}"/></marker>')
    L.append('</defs>')
    L.append(f'<text x="{W/2}" y="40" text-anchor="middle" font-size="30" font-weight="700" fill="#1f2937">Face-Detect MLOps — System Overview (best-of-breed, numbered data flow)</text>')
    for x,y,w,h,t,fill,st in ZONES:
        L.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{st}" stroke-width="1.4"/>')
        L.append(f'<text x="{x+16}" y="{y+24}" font-size="16" font-weight="700" fill="#384150">{html.escape(t)}</text>')
    for s,d,lbl,col,dash in E:
        pts=route(s,d); da=' stroke-dasharray="5,4"' if dash else ''
        path=" ".join(f"{x:.0f},{y:.0f}" for x,y in pts)
        L.append(f'<polyline points="{path}" fill="none" stroke="{col}" stroke-width="1.9"{da} marker-end="url(#m{col.replace("#","")})"/>')
        if lbl:
            mx,my=pts[len(pts)//2]; wd=len(lbl)*6.2+8
            L.append(f'<rect x="{mx-wd/2:.0f}" y="{my-9:.0f}" width="{wd:.0f}" height="15" rx="3" fill="{ZONE_AT(my)}" opacity="0.96"/>')
            L.append(f'<text x="{mx:.0f}" y="{my+2:.0f}" text-anchor="middle" font-size="10.5" fill="#3a4252">{html.escape(lbl)}</text>')
    for id,(x,y,k,ic,label) in N.items():
        if k=='i':
            L.append(f'<image x="{x-IW/2}" y="{y-IH/2}" width="{IW}" height="{IH}" xlink:href="data:image/png;base64,{_b64(f"{IC}/{ic}.png")}"/>')
            lines=label.split("\n")
            for i,ln in enumerate(lines):
                L.append(f'<text x="{x}" y="{y+IH/2+13+i*12:.0f}" text-anchor="middle" font-size="10.5" font-weight="600" fill="#2b3240">{html.escape(ln)}</text>')
        else:
            L.append(f'<rect x="{x-AW/2}" y="{y-AH/2}" width="{AW}" height="{AH}" rx="9" fill="{ic}" stroke="#8a93a3" stroke-width="1.3"/>')
            lines=label.split("\n"); y0=y-(len(lines)-1)*7
            for i,ln in enumerate(lines):
                L.append(f'<text x="{x}" y="{y0+i*14+4:.0f}" text-anchor="middle" font-size="11" font-weight="700" fill="#2b3240">{html.escape(ln)}</text>')
    L.append('</svg>'); return "\n".join(L)

svg_str=svg()
open(f"{OUTDIR}/01-overview.svg","w").write(svg_str)
cairosvg.svg2png(bytestring=svg_str.encode(),write_to=f"{OUTDIR}/01-overview.png",output_width=2400)
print("PNG written")

def drawio():
    cells=['<mxCell id="0"/>','<mxCell id="1" parent="0"/>']; cid=2; ref={}
    for x,y,w,h,t,fill,st in ZONES:
        cells.append(f'<mxCell id="z{cid}" value="{html.escape(t)}" style="rounded=1;fillColor={fill};strokeColor={st};verticalAlign=top;align=left;spacingLeft=14;spacingTop=6;fontSize=15;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'); cid+=1
    for id,(x,y,k,ic,label) in N.items():
        ref[id]=f"n{cid}"; lbl=html.escape(label.replace(chr(10)," "))
        if k=='i':
            style=f"shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;image=data:image/png,{_b64(f'{IC}/{ic}.png')};fontSize=10;"
            cells.append(f'<mxCell id="{ref[id]}" value="{lbl}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x-IW/2}" y="{y-IH/2}" width="{IW}" height="{IH}" as="geometry"/></mxCell>')
        else:
            style=f"rounded=1;fillColor={ic};strokeColor=#8a93a3;fontSize=11;fontStyle=1;whiteSpace=wrap;"
            cells.append(f'<mxCell id="{ref[id]}" value="{lbl}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x-AW/2}" y="{y-AH/2}" width="{AW}" height="{AH}" as="geometry"/></mxCell>')
        cid+=1
    for s,d,lbl,col,dash in E:
        da="dashed=1;" if dash else ""
        style=f"edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor={col};{da}fontSize=10;endArrow=block;html=1;"
        cells.append(f'<mxCell id="e{cid}" value="{html.escape(lbl)}" style="{style}" edge="1" parent="1" source="{ref[s]}" target="{ref[d]}"><mxGeometry relative="1" as="geometry"/></mxCell>'); cid+=1
    model=f'<mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{W}" pageHeight="{H}"><root>{"".join(cells)}</root></mxGraphModel>'
    return f'<mxfile host="app.diagrams.net"><diagram name="Overview" id="overview">{model}</diagram></mxfile>'

open(f"{OUTDIR}/01-overview.drawio","w").write(drawio())
print("drawio written")
