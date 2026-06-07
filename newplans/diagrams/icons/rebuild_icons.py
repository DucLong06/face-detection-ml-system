#!/usr/bin/env python3
"""Rebuild /tmp/icons/png after /tmp wipe: resources logos + downloads + tiles + user logos (transparent)."""
import os, re, urllib.request, glob
from collections import deque
from PIL import Image
import cairosvg

DST="/tmp/icons/png"; os.makedirs(DST,exist_ok=True)
RES="/home/longhd/.local/lib/python3.12/site-packages/resources"
USERD="/mnt/data/mlops/Long-project/face-detect-gke/plans/260604-2213-mlops-l2-l3-rag-complete-build/diagrams/icons"

# 1) bundled full-color logos from diagrams resources
bundled={"github":"github","argocd":"argocd","istio":"istio","kafka":"kafka","spark":"spark",
 "flink":"flink","trino":"trino","airflow":"airflow","mlflow":"mlflow","kubeflow":"kubeflow",
 "prometheus":"prometheus","grafana":"grafana","thanos":"thanos","jaeger":"jaeger",
 "elasticsearch":"elasticsearch","kibana":"kibana","logstash":"logstash","filebeat":"filebeat",
 "postgresql":"postgresql","redis":"redis","flagger":"flagger","terraform":"terraform",
 "ansible":"ansible","docker":"docker","fastapi":"fastapi","certmanager":"cert-manager"}
import shutil
for key,fn in bundled.items():
    f=glob.glob(f"{RES}/**/{fn}.png",recursive=True)
    if f: shutil.copy(f[0],f"{DST}/{key}.png")
    else: print("no resource",key)

# 2) downloads (simple-icons monochrome -> brand color; gilbarbara/cncf colored)
def dl(key,url,color=None):
    try:
        raw=urllib.request.urlopen(url,timeout=15).read().decode()
        if "<svg" not in raw: return False
        if color:
            raw=raw.replace("currentColor",color)
            if "fill=" not in raw.split(">",1)[0]: raw=re.sub(r"<svg ",f'<svg fill="{color}" ',raw,1)
        cairosvg.svg2png(bytestring=raw.encode(),write_to=f"{DST}/{key}.png",output_width=256,output_height=256,background_color=None)
        return True
    except Exception as e:
        return False
SI="https://cdn.jsdelivr.net/npm/simple-icons/icons/{}.svg"
GB="https://cdn.jsdelivr.net/gh/gilbarbara/logos/logos/{}.svg"
CNCF="https://cdn.jsdelivr.net/gh/cncf/artwork/projects/{}/icon/color/{}-icon-color.svg"
downloads={
 "minio":(SI.format("minio"),"#C72E49"),"nvidia":(SI.format("nvidia"),"#76B900"),
 "keycloak":(SI.format("keycloak"),"#4D7EA8"),"ollama":(SI.format("ollama"),"#101010"),
 "kubernetes":(SI.format("kubernetes"),"#326CE5"),"qdrant":(SI.format("qdrant"),"#DC244C"),
 "opentelemetry":(SI.format("opentelemetry"),"#425CC7"),"githubactions":(SI.format("githubactions"),"#2088FF"),
 "vault":(SI.format("vaultproject") if False else SI.format("vault"),"#000000"),"ray":(SI.format("ray"),"#028CF0"),
 "vllm":(SI.format("vllm"),"#30A2FF"),"yolo":(SI.format("ultralytics"),"#0B23A9"),
 "typesense":(GB.format("typesense"),None),"kyverno":(CNCF.format("kyverno","kyverno"),None),
 "argo":(CNCF.format("argo","argo"),None),"knative":(SI.format("knative"),"#0865AD"),
}
for k,(u,c) in downloads.items():
    if not dl(k,u,c): print("DL FAIL (will need fallback):",k)

# 3) conceptual fallback tiles
tiles={"gpu":("#76B900","GPU pool"),"kueue":("#326CE5","Kueue"),"approval":("#0E7C66","Approval"),
 "embedding":("#7c3aed","Embed"),"alertmanager":("#E6522C","Alertmgr"),"fdimage":("#0b6fb8","FD image"),
 "guardrails":("#1F8A4C","Guardrails")}
for n,(c,l) in tiles.items():
    init=l.split()[0][:9]; fs=20 if len(init)<=6 else 15
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><rect x="6" y="6" width="108" height="108" rx="22" fill="{c}"/><text x="60" y="68" font-family="Arial" font-size="{fs}" font-weight="700" fill="#fff" text-anchor="middle">{init}</text></svg>'
    cairosvg.svg2png(bytestring=svg.encode(),write_to=f"{DST}/{n}.png",output_width=256,output_height=256)

# 4) USER logos (transparent bg via border flood-fill) — overrides any fallback
def debg(im):
    im=im.convert("RGBA"); w,h=im.size; px=im.load()
    def bg(p): return p[3]>0 and p[0]>=238 and p[1]>=238 and p[2]>=238
    seen=[[False]*w for _ in range(h)]; q=deque()
    for x in range(w):
        for y in (0,h-1):
            if bg(px[x,y]): seen[y][x]=True; q.append((x,y))
    for y in range(h):
        for x in (0,w-1):
            if bg(px[x,y]) and not seen[y][x]: seen[y][x]=True; q.append((x,y))
    while q:
        x,y=q.popleft(); px[x,y]=(255,255,255,0)
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<w and 0<=ny<h and not seen[ny][nx] and bg(px[nx,ny]):
                seen[ny][nx]=True; q.append((nx,ny))
    return im
users=["alibidetect","debezium","evidently","feast","greatexpectations","iceberg","iter8",
 "kafkaconnect","katib","keda","kserve","lakefs","langfuse","oauth2proxy","openmetadata",
 "ragflow","schemaregistry","weaviate"]
for n in users:
    p=f"{USERD}/{n}.png"
    if not os.path.exists(p): print("USER MISS",n); continue
    im=debg(Image.open(p)); w,h=im.size; side=max(w,h)
    cv=Image.new("RGBA",(side,side),(0,0,0,0)); cv.paste(im,((side-w)//2,(side-h)//2),im)
    cv.resize((256,256)).save(f"{DST}/{n}.png")
print("ICON COUNT:",len(glob.glob(f"{DST}/*.png")))
