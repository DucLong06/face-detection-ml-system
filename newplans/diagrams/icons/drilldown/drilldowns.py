#!/usr/bin/env python3
"""Per-zone drill-down diagrams -> .drawio (editable) + .png. Decisions baked in:
 lakeFS Iceberg REST Catalog (no Nessie), shared GPU pool (MIG + Kueue), human approval gate."""
import base64, os, html, cairosvg
IC="/tmp/icons/png"
OUT="/mnt/data/mlops/Long-project/face-detect-gke/plans/260604-2213-mlops-l2-l3-rag-complete-build/diagrams/icons/drilldown"
os.makedirs(OUT,exist_ok=True)
IW,IH=56,56; AW,AH=128,54
def _b64(p): return base64.b64encode(open(p,"rb").read()).decode()

def build(outname,title,W,H,ZONES,N,E):
    def anchors(id):
        x,y,k,_,_=N[id]; w=IW if k=='i' else AW; h=IH if k=='i' else AH
        return dict(x=x,y=y,l=(x-w/2,y),r=(x+w/2,y),t=(x,y-h/2),b=(x,y+h/2))
    def route(s,d):
        a,b=anchors(s),anchors(d); dx=b['x']-a['x']; dy=b['y']-a['y']
        if abs(dy)<24:
            p=[a['r'],b['l']] if dx>=0 else [a['l'],b['r']]; mx=(p[0][0]+p[1][0])/2
            return [p[0],(mx,p[0][1]),(mx,p[1][1]),p[1]]
        st=a['b'] if dy>0 else a['t']; en=b['t'] if dy>0 else b['b']; my=(st[1]+en[1])/2
        return [st,(st[0],my),(en[0],my),en]
    def zat(yy):
        for x,y,w,h,t,f,s in ZONES:
            if y<=yy<=y+h: return f
        return "#ffffff"
    # SVG
    L=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" font-family="DejaVu Sans, Arial">',
       f'<rect width="{W}" height="{H}" fill="#fff"/>','<defs>']
    for c in set(e[3] for e in E):
        L.append(f'<marker id="m{c.replace("#","")}" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="{c}"/></marker>')
    L.append('</defs>')
    L.append(f'<text x="{W/2}" y="38" text-anchor="middle" font-size="26" font-weight="700" fill="#1f2937">{html.escape(title)}</text>')
    for x,y,w,h,t,f,s in ZONES:
        L.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{f}" stroke="{s}" stroke-width="1.3" stroke-dasharray="6,4"/>')
        L.append(f'<text x="{x+14}" y="{y+22}" font-size="14" font-weight="700" fill="#384150">{html.escape(t)}</text>')
    for s,d,lbl,col,dash in E:
        pts=route(s,d); da=' stroke-dasharray="5,4"' if dash else ''
        path=" ".join(f"{x:.0f},{y:.0f}" for x,y in pts)
        L.append(f'<polyline points="{path}" fill="none" stroke="{col}" stroke-width="1.9"{da} marker-end="url(#m{col.replace("#","")})"/>')
        if lbl:
            mx,my=pts[len(pts)//2]; wd=len(lbl)*6.2+8
            L.append(f'<rect x="{mx-wd/2:.0f}" y="{my-9:.0f}" width="{wd:.0f}" height="15" rx="3" fill="{zat(my)}" opacity="0.96"/>')
            L.append(f'<text x="{mx:.0f}" y="{my+2:.0f}" text-anchor="middle" font-size="10.5" fill="#3a4252">{html.escape(lbl)}</text>')
    for id,(x,y,k,ic,label) in N.items():
        if k=='i':
            L.append(f'<image x="{x-IW/2}" y="{y-IH/2}" width="{IW}" height="{IH}" xlink:href="data:image/png;base64,{_b64(f"{IC}/{ic}.png")}"/>')
            for i,ln in enumerate(label.split("\n")):
                L.append(f'<text x="{x}" y="{y+IH/2+13+i*12:.0f}" text-anchor="middle" font-size="10.5" font-weight="600" fill="#2b3240">{html.escape(ln)}</text>')
        else:
            L.append(f'<rect x="{x-AW/2}" y="{y-AH/2}" width="{AW}" height="{AH}" rx="9" fill="{ic}" stroke="#8a93a3" stroke-width="1.3"/>')
            lines=label.split("\n"); y0=y-(len(lines)-1)*7
            for i,ln in enumerate(lines):
                L.append(f'<text x="{x}" y="{y0+i*14+4:.0f}" text-anchor="middle" font-size="11" font-weight="700" fill="#2b3240">{html.escape(ln)}</text>')
    L.append('</svg>'); svg="\n".join(L)
    cairosvg.svg2png(bytestring=svg.encode(),write_to=f"{OUT}/{outname}.png",output_width=2200)
    # drawio
    cells=['<mxCell id="0"/>','<mxCell id="1" parent="0"/>']; cid=2; ref={}
    for x,y,w,h,t,f,s in ZONES:
        cells.append(f'<mxCell id="z{cid}" value="{html.escape(t)}" style="rounded=1;dashed=1;fillColor={f};strokeColor={s};verticalAlign=top;align=left;spacingLeft=12;spacingTop=6;fontSize=13;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'); cid+=1
    for id,(x,y,k,ic,label) in N.items():
        ref[id]=f"n{cid}"; lbl=html.escape(label.replace(chr(10)," "))
        if k=='i':
            cells.append(f'<mxCell id="{ref[id]}" value="{lbl}" style="shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;image=data:image/png,{_b64(f"{IC}/{ic}.png")};fontSize=10;" vertex="1" parent="1"><mxGeometry x="{x-IW/2}" y="{y-IH/2}" width="{IW}" height="{IH}" as="geometry"/></mxCell>')
        else:
            cells.append(f'<mxCell id="{ref[id]}" value="{lbl}" style="rounded=1;fillColor={ic};strokeColor=#8a93a3;fontSize=11;fontStyle=1;whiteSpace=wrap;" vertex="1" parent="1"><mxGeometry x="{x-AW/2}" y="{y-AH/2}" width="{AW}" height="{AH}" as="geometry"/></mxCell>')
        cid+=1
    for s,d,lbl,col,dash in E:
        da="dashed=1;" if dash else ""
        cells.append(f'<mxCell id="e{cid}" value="{html.escape(lbl)}" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor={col};{da}fontSize=10;endArrow=block;html=1;" edge="1" parent="1" source="{ref[s]}" target="{ref[d]}"><mxGeometry relative="1" as="geometry"/></mxCell>'); cid+=1
    model=f'<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" page="1" pageWidth="{W}" pageHeight="{H}"><root>{"".join(cells)}</root></mxGraphModel>'
    open(f"{OUT}/{outname}.drawio","w").write(f'<mxfile host="app.diagrams.net"><diagram name="{outname}" id="{outname}">{model}</diagram></mxfile>')
    print("built",outname)

def ni(N,id,x,y,ic,l): N[id]=(x,y,'i',ic,l)
def na(N,id,x,y,f,l): N[id]=(x,y,'a',f,l)

# ============================ ZONE 1: DATA ============================
N={};
na(N,"wider",110,230,"#cfe0f3","WIDER FACE\n(batch)")
na(N,"camera",110,640,"#cfe0f3","Camera / API\n(stream)")
na(N,"appdb",110,780,"#cfe0f3","App DB\n(CDC)")
ni(N,"bronze",440,230,"minio","MinIO Bronze\n(S3)")
ni(N,"silver",820,230,"minio","MinIO Silver\n(S3)")
ni(N,"gold",1180,230,"iceberg","Iceberg Gold")
ni(N,"lakefs",1450,230,"lakefs","lakeFS REST\ncatalog + version")
ni(N,"trino",1690,230,"trino","Trino")
ni(N,"pg",1930,230,"postgresql","PostgreSQL DW")
ni(N,"redisf",1930,360,"redis","Feast online")
ni(N,"spark1",620,430,"spark","Spark\ntransform")
ni(N,"ge1",620,360,"greatexpectations","GE #1")
ni(N,"spark2",1000,430,"spark","Spark\ntransform")
ni(N,"ge2",1000,360,"greatexpectations","GE #2")
ni(N,"kafka",450,640,"kafka","Kafka topics\nraw/validated/cdc")
ni(N,"schema",650,600,"schemaregistry","Schema Registry")
ni(N,"debezium",450,790,"debezium","Debezium")
ni(N,"connect",650,790,"kafkaconnect","Kafka Connect")
ni(N,"flink",950,650,"flink","Flink validate")
ni(N,"airflow",1180,650,"airflow","Airflow")
ni(N,"argoev",1340,650,"argo","Argo Events")
ni(N,"openmeta",1600,650,"openmetadata","OpenMetadata\ncatalog+lineage+RBAC")
Z=[(300,150,1820,250,"ns: data-storage  ·  lakehouse (storage layers)","#fff5e6","#e0a86a"),
   (300,330,860,170,"ns: data-processing  (Spark transforms)","#eef0fb","#7d8fd6"),
   (300,560,560,300,"ns: data-ingestion","#e9f3fe","#7badd6"),
   (880,580,220,160,"ns: data-streaming","#eef7ee","#86bf86"),
   (1140,580,300,160,"ns: data-orchestration","#f3eefb","#b193d6"),
   (1480,580,360,160,"ns: data-catalog","#fde9f0","#d98ab0")]
E=[("wider","bronze","(1a) batch","#1864ab",0),("camera","kafka","(1b) stream","#1864ab",0),
   ("appdb","debezium","(1c) cdc","#1864ab",0),("debezium","connect","","#c92a2a",0),("connect","kafka","","#c92a2a",0),
   ("schema","kafka","","#9aa4b2",1),("kafka","flink","(2) validate","#1864ab",0),
   ("flink","bronze","(3) land","#1864ab",0),("flink","redisf","sidecar: online feat","#e8590c",1),
   ("bronze","spark1","(4) read","#1864ab",0),("spark1","silver","write","#1864ab",0),("ge1","silver","GE#1","#2b8a3e",1),
   ("silver","spark2","(5) read","#1864ab",0),("spark2","gold","write","#1864ab",0),("ge2","gold","GE#2","#2b8a3e",1),
   ("gold","lakefs","(6) version","#1864ab",0),("gold","trino","","#1864ab",0),("trino","pg","DW","#1864ab",0),
   ("gold","openmeta","lineage","#2b8a3e",1),("airflow","spark1","schedule","#9aa4b2",1),("airflow","spark2","","#9aa4b2",1),
   ("ge2","argoev","fail→alert","#c92a2a",1)]
build("zone-1-data","Drill-down — Data Pipeline (L2 lakehouse: batch+stream+CDC)",2240,920,Z,N,E)

# ============================ ZONE 2: TRAINING ============================
N={}
ni(N,"trino",110,300,"trino","Gold via Trino\n(Iceberg)")
ni(N,"feast",330,300,"feast","Feast offline")
ni(N,"redisf",330,440,"redis","Feast online")
ni(N,"notebooks",560,200,"kubeflow","Notebooks")
ni(N,"kfp",560,330,"kubeflow","Kubeflow Pipeline\nload→prep→train→eval→register→export")
ni(N,"katib",880,260,"katib","Katib HPO\n(trials fan-out)")
ni(N,"ray",880,400,"ray","Ray / KubeRay\ntrain (GPU / CPU-slow)")
ni(N,"gpu",880,540,"gpu","GPU pool (optional)\nCPU fallback (slow)")
ni(N,"mlflow",1150,330,"mlflow","MLflow\ntracking + registry")
ni(N,"onnx",1400,300,"kserve","ONNX export (CPU)")
ni(N,"trt",1400,430,"nvidia","TensorRT INT8\n(GPU only)")
ni(N,"store",1620,330,"minio","Model store\n(MinIO/Iceberg)")
Z=[(80,150,420,360,"ns: data-storage / feast (inputs)","#fff5e6","#e0a86a"),
   (520,150,780,440,"ns: ml-platform","#eef0fb","#7d8fd6"),
   (1320,250,460,230,"export + model store","#eef7ee","#86bf86")]
E=[("trino","feast","(1) materialize","#2b8a3e",0),("feast","redisf","online","#2b8a3e",1),
   ("feast","kfp","(2) load features","#2b8a3e",0),("notebooks","kfp","(3) author","#9aa4b2",1),
   ("kfp","katib","(4) HPO","#2b8a3e",0),("kfp","ray","(5) train","#2b8a3e",0),("ray","gpu","uses","#9aa4b2",1),
   ("katib","ray","best trial","#2b8a3e",1),("kfp","mlflow","(6) register","#2b8a3e",0),
   ("mlflow","onnx","(7) export","#2b8a3e",0),("onnx","trt","opt (GPU)","#2b8a3e",1),
   ("onnx","store","(8) store","#2b8a3e",0),("trt","store","","#2b8a3e",1)]
build("zone-2-training","Drill-down — Training Pipeline (L3: Kubeflow·Katib·Ray·MLflow·Feast)",1840,660,Z,N,E)

# ============================ ZONE 3: SERVING ============================
N={}
na(N,"user",110,330,"#f2dcc2","End User")
ni(N,"istio",300,330,"istio","Istio gateway\nmTLS · route")
ni(N,"kserve",520,330,"kserve","KServe\nInferenceService")
ni(N,"knative",520,470,"knative","Knative\nscale-to-zero")
ni(N,"v1",760,250,"nvidia","Model v1 (Triton)\nprimary 90%")
ni(N,"v2",760,410,"nvidia","Model v2 (Triton)\ncanary 10%")
ni(N,"gpu",760,560,"gpu","GPU pool (optional)\nCPU = ONNX")
ni(N,"flagger",1020,250,"flagger","Flagger canary\n5→25→50→100%")
ni(N,"iter8",1020,410,"iter8","Iter8 A/B + SLO")
ni(N,"keda",1240,330,"keda","KEDA autoscale")
ni(N,"mlflow",520,180,"mlflow","MLflow registry")
ni(N,"redisf",300,490,"redis","Feast online")
ni(N,"prom",1240,490,"prometheus","Prometheus")
Z=[(80,250,160,170,"ingress","#fff3e6","#e0a86a"),
   (260,120,1120,520,"ns: model-serving","#fff5e6","#e0a86a")]
E=[("user","istio","(1) request","#b8741a",0),("istio","kserve","(2) route","#b8741a",0),
   ("mlflow","kserve","(4) load model","#b8741a",1),("redisf","kserve","(5) features","#b8741a",1),
   ("kserve","v1","(3) runtime","#b8741a",0),("kserve","v2","","#b8741a",0),("knative","kserve","scale-0","#9aa4b2",1),
   ("v1","gpu","MIG","#9aa4b2",1),("v2","gpu","MIG","#9aa4b2",1),
   ("flagger","v1","split","#c92a2a",1),("flagger","v2","split","#c92a2a",1),("iter8","flagger","experiment","#c92a2a",1),
   ("kserve","prom","(7) metrics","#059669",1),("prom","keda","rate/lag","#9aa4b2",1),("keda","kserve","(8) scale","#9aa4b2",1)]
build("zone-3-serving","Drill-down — Serving (L3: KServe+Knative+Triton/MIG+Flagger+Iter8+KEDA)",1500,700,Z,N,E)

# ============================ ZONE 4: DRIFT LOOP ============================
N={}
ni(N,"kserve",160,330,"kserve","KServe + Triton\n(production)")
ni(N,"evidently",400,250,"evidently","Evidently\ndata/pred drift")
ni(N,"alibi",400,410,"alibidetect","Alibi Detect\noutlier/adversarial")
ni(N,"prom",640,330,"prometheus","Prometheus\n+ Thanos")
na(N,"decide",870,330,"#ffe0b3","drift_score\n> 0.5 ?")
ni(N,"alertmgr",1100,330,"alertmanager","Alertmanager")
ni(N,"argoev",1330,330,"argo","Argo Events")
ni(N,"kfp",1560,330,"kubeflow","Kubeflow retrain\nfetch Gold→train(Ray)→eval(GE)")
ni(N,"datapin",1560,470,"lakefs","lakeFS + Iceberg\nsnapshot (reproducible)")
ni(N,"mlflow",1560,200,"mlflow","MLflow Staging\n(F1>baseline)")
na(N,"approval",1300,140,"#cdeccd","Human approval\n(gate to Prod)")
ni(N,"flagger",760,520,"flagger","Flagger canary 5%")
Z=[(120,160,560,360,"ns: ml-monitoring + monitoring","#fdecec","#d98a8a"),
   (1020,160,720,400,"ns: data-orchestration + ml-platform","#eef0fb","#7d8fd6")]
E=[("kserve","evidently","(1) predictions","#c92a2a",0),("kserve","alibi","inputs","#c92a2a",1),
   ("evidently","prom","(2) drift_score","#c92a2a",0),("alibi","prom","","#c92a2a",1),
   ("prom","decide","(3)","#c92a2a",0),("decide","alertmgr","(4) >0.5 alert","#c92a2a",0),
   ("alertmgr","argoev","(5) webhook","#c92a2a",0),("argoev","kfp","(6) retrain","#c92a2a",0),
   ("datapin","kfp","pin data","#9aa4b2",1),("kfp","mlflow","(7) Staging","#2b8a3e",0),
   ("mlflow","approval","(8) request","#0e7c66",0),("approval","flagger","(9) approved→canary","#0e7c66",0),
   ("flagger","kserve","(10) promote / rollback","#c92a2a",1)]
build("zone-4-drift-loop","Drill-down — Drift→Retrain→Canary Loop * (closed loop, human-gated)",1800,640,Z,N,E)

# ============================ ZONE 5: RAG ============================
N={}
# indexing (top)
na(N,"docs",110,200,"#e6dcf3","Docs: reports /\nrunbooks / metadata")
ni(N,"embed_i",330,200,"embedding","Embed (BGE)")
ni(N,"qdrant",560,200,"qdrant","Qdrant\nvector DB")
ni(N,"typesense",560,330,"typesense","Typesense\nkeyword")
# query (bottom)
na(N,"q",110,470,"#e6dcf3","User question")
ni(N,"ragflow",330,470,"ragflow","RAGFlow\norchestrator")
ni(N,"merge",780,470,"embedding","merge + rerank")
ni(N,"guard",1010,470,"guardrails","NeMo Guardrails\nin + out")
ni(N,"vllm",1250,470,"vllm","vLLM (GPU)\nor Ollama (CPU)")
ni(N,"langfuse",1250,330,"langfuse","Langfuse\ntrace/cost/eval")
Z=[(80,120,720,300,"Phase A — offline indexing","#f0eaf8","#b193d6"),
   (80,400,1420,180,"Phase B — online query","#f3eefb","#b193d6")]
E=[("docs","embed_i","chunk","#7c3aed",0),("embed_i","qdrant","index","#7c3aed",0),("embed_i","typesense","index","#7c3aed",1),
   ("q","ragflow","(1) ask","#7c3aed",0),("ragflow","qdrant","(3) vector","#7c3aed",0),("ragflow","typesense","(4) keyword","#7c3aed",0),
   ("qdrant","merge","(5) context","#7c3aed",0),("typesense","merge","","#7c3aed",0),
   ("merge","guard","(6) guard-in","#7c3aed",0),("guard","vllm","(7) generate","#7c3aed",0),
   ("vllm","guard","(8) guard-out","#7c3aed",1),("guard","q","(9) response","#7c3aed",0),
   ("vllm","langfuse","(10) trace","#059669",1)]
build("zone-5-rag","Drill-down — RAG/LLM (indexing + query, Guardrails wrap, vLLM)",1560,640,Z,N,E)

# ============================ ZONE 6: PLATFORM / IaC + APP DEPLOY (app-centric) ============================
N={}
# CI/CD row — building THE app image
na(N,"dev",120,255,"#dfe7f0","Developer")
na(N,"appsrc",300,255,"#dbe7f7","face-detect app\nFastAPI + YOLOv11 code")
ni(N,"github",480,255,"github","GitHub")
ni(N,"gha",630,255,"githubactions","GitHub Actions\nbuild + test")
ni(N,"fdimage",790,255,"fdimage","face-detect\nimage")
ni(N,"registry",950,255,"docker","Image registry")
ni(N,"argocd",1130,300,"argocd","ArgoCD\nCD (GitOps)")
# GKE runtime — THE running app
ni(N,"istio",1310,290,"istio","Istio gateway\nmTLS")
ni(N,"kserve",1500,255,"kserve","KServe\n(L1: FastAPI)")
ni(N,"triton",1670,255,"nvidia","Triton\nGPU:TensorRT / CPU:ONNX")
ni(N,"yolo",1580,380,"yolo","YOLOv11 model")
na(N,"enduser",1310,400,"#f2dcc2","End User")
# IaC (provision the cluster the app runs on)
ni(N,"terraform",1330,545,"terraform","Terraform\nGKE + GPU pool")
ni(N,"ansible",1500,545,"ansible","Ansible\nVM config")
# auth + policy + secrets (support)
na(N,"user",150,600,"#dfe7f0","Ops user")
ni(N,"keycloak",320,600,"keycloak","Keycloak OIDC")
ni(N,"oauth",490,600,"oauth2proxy","OAuth2 Proxy")
na(N,"uis",680,600,"#e7eefc","Ops UIs\n1-cookie SSO")
ni(N,"kyverno",320,730,"kyverno","Kyverno")
ni(N,"vault",490,730,"vault","Vault + ESO")
ni(N,"certmgr",650,730,"certmanager","cert-manager")
na(N,"gov",860,730,"#fff0d6","Governance baseline\n(applied to ALL ns)")
Z=[(70,175,1010,165,"CI/CD — GitHub Actions (build the app image)","#eef2f7","#9aa4b2"),
   (1230,170,720,300,"Google Kubernetes Engine + GPU pool (MIG)","#e9f3fe","#7badd6"),
   (1250,210,690,205,"ns: model-serving  ·  the running app","#fff5e6","#e0a86a"),
   (1250,495,420,110,"IaC (provision)","#eef7ee","#86bf86"),
   (70,540,1010,250,"auth (SSO) + policy + secrets","#f3eefb","#b193d6")]
E=[("dev","appsrc","writes","#5b6472",0),("appsrc","github","push code","#5b6472",0),
   ("github","gha","trigger","#5b6472",0),("gha","fdimage","build+test","#5b6472",0),
   ("fdimage","registry","push image","#5b6472",0),("registry","argocd","image + manifest","#5b6472",0),
   ("argocd","kserve","(deploy) face-detect app","#5b6472",0),
   ("enduser","istio","request","#b8741a",0),("istio","kserve","route","#b8741a",0),
   ("kserve","triton","runtime","#b8741a",0),("triton","yolo","inference","#1864ab",0),
   ("terraform","ansible","then","#9aa4b2",1),("terraform","istio","provision GKE+GPU","#9aa4b2",1),
   ("user","keycloak","login","#7c3aed",0),("keycloak","oauth","","#7c3aed",0),("oauth","uis","SSO 1-cookie","#7c3aed",0),
   ("kyverno","gov","policy","#9aa4b2",1),("vault","gov","secrets","#9aa4b2",1),("certmgr","gov","TLS","#9aa4b2",1)]
build("zone-6-platform","Drill-down — Platform/IaC + App Deploy (face-detection: code -> image -> GKE)",1990,840,Z,N,E)

# ============================ ZONE 7: OBSERVABILITY ============================
N={}
na(N,"svcs",110,360,"#dfeeea","All services\n(OTLP)")
ni(N,"otel",330,360,"opentelemetry","OTel Collector")
ni(N,"prom",600,230,"prometheus","Prometheus")
ni(N,"thanos",820,230,"thanos","Thanos (long-term)")
ni(N,"grafana",1040,230,"grafana","Grafana")
ni(N,"alertmgr",820,330,"alertmanager","Alertmanager")
na(N,"drift",1040,330,"#fdd9d9","→ Drift loop")
ni(N,"filebeat",600,460,"filebeat","Filebeat")
ni(N,"logstash",790,460,"logstash","Logstash")
ni(N,"elastic",980,460,"elasticsearch","Elasticsearch")
ni(N,"kibana",1170,460,"kibana","Kibana")
ni(N,"jaeger",600,590,"jaeger","Jaeger")
Z=[(540,170,720,170,"ns: monitoring (metrics + alert)","#eafaf0","#86c9a8"),
   (540,400,820,130,"ns: logging (ELK)","#fff5e6","#e0a86a"),
   (540,550,300,110,"ns: tracing","#e9f3fe","#7badd6")]
E=[("svcs","otel","(1) OTLP","#059669",0),("otel","prom","metrics","#059669",0),
   ("prom","thanos","(2) store","#059669",0),("thanos","grafana","viz","#059669",0),
   ("prom","alertmgr","alert","#c92a2a",0),("alertmgr","drift","(5)","#c92a2a",1),
   ("otel","filebeat","logs","#b8741a",0),("filebeat","logstash","(3)","#b8741a",0),("logstash","elastic","","#b8741a",0),("elastic","kibana","","#b8741a",0),
   ("otel","jaeger","(4) traces","#7c3aed",0)]
build("zone-7-observability","Drill-down — Observability (OTel → metrics / logs / traces)",1380,700,Z,N,E)
print("ALL DRILLDOWNS DONE")
