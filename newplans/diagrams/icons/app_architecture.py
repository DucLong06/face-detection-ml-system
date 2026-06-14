#!/usr/bin/env python3
"""App-centric architecture diagram — upgraded version of images/architecture.png.
Shows: Dev -> GitHub -> GitHub Actions -> face-detect image -> registry -> ArgoCD -> GKE(model-serving),
End User request path, and observability (metrics/traces/logs) from the app. Emits .drawio + .png."""
import base64, os, html, cairosvg
IC="/tmp/icons/png"
OUT="/mnt/data/mlops/Long-project/face-detect-gke/plans/260604-2213-mlops-l2-l3-rag-complete-build/diagrams/icons"
IW,IH=56,56; AW,AH=128,54
def _b64(p): return base64.b64encode(open(p,"rb").read()).decode()

def build(outname,title,W,H,ZONES,N,E):
    def anc(id):
        x,y,k,_,_=N[id]; w=IW if k=='i' else AW; h=IH if k=='i' else AH
        return dict(x=x,y=y,l=(x-w/2,y),r=(x+w/2,y),t=(x,y-h/2),b=(x,y+h/2))
    def route(s,d):
        a,b=anc(s),anc(d); dy=b['y']-a['y']; dx=b['x']-a['x']
        if abs(dy)<24:
            p=[a['r'],b['l']] if dx>=0 else [a['l'],b['r']]; mx=(p[0][0]+p[1][0])/2
            return [p[0],(mx,p[0][1]),(mx,p[1][1]),p[1]]
        st=a['b'] if dy>0 else a['t']; en=b['t'] if dy>0 else b['b']; my=(st[1]+en[1])/2
        return [st,(st[0],my),(en[0],my),en]
    def zat(yy):
        best="#ffffff"
        for x,y,w,h,t,f,s in ZONES:
            if y<=yy<=y+h: best=f
        return best
    L=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" font-family="DejaVu Sans, Arial">',f'<rect width="{W}" height="{H}" fill="#fff"/>','<defs>']
    for c in set(e[3] for e in E):
        L.append(f'<marker id="m{c.replace("#","")}" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto"><polygon points="0 0,9 3.5,0 7" fill="{c}"/></marker>')
    L.append('</defs>')
    L.append(f'<text x="{W/2}" y="40" text-anchor="middle" font-size="28" font-weight="700" fill="#1f2937">{html.escape(title)}</text>')
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

N={}
# IaC (top) + End User (top-right)
ni(N,"terraform",880,110,"terraform","Terraform")
ni(N,"ansible",1040,110,"ansible","Ansible")
na(N,"enduser",1700,110,"#f2dcc2","End User")
# CI/CD pipeline (left, vertical) + developer outside
na(N,"dev",100,470,"#dfe7f0","Developer")
ni(N,"github",300,330,"github","GitHub")
ni(N,"gha",300,470,"githubactions","GitHub Actions\nbuild + test")
ni(N,"fdimage",300,610,"fdimage","face-detect\nimage")
ni(N,"registry",300,740,"docker","Image registry")
ni(N,"argocd",560,470,"argocd","ArgoCD\nCD (GitOps)")
# GKE model-serving (center) — THE APP
ni(N,"istio",900,360,"istio","Istio ingress\n(gateway)")
ni(N,"kserve",1090,360,"kserve","KServe\n(FastAPI L1)")
ni(N,"triton",1290,360,"nvidia","Triton\nGPU:TensorRT / CPU:ONNX")
ni(N,"yolo",1090,500,"yolo","YOLOv11 model")
# monitoring
ni(N,"prom",960,720,"prometheus","Prometheus")
ni(N,"grafana",1140,720,"grafana","Grafana")
# tracing
ni(N,"otel",1340,720,"opentelemetry","OTel Collector")
ni(N,"jaeger",1500,720,"jaeger","Jaeger")
# logging (right column)
ni(N,"filebeat",1760,340,"filebeat","Filebeat")
ni(N,"logstash",1760,470,"logstash","Logstash")
ni(N,"elastic",1760,600,"elasticsearch","Elasticsearch")
ni(N,"kibana",1760,730,"kibana","Kibana")

Z=[(180,270,560,560,"CI/CD Pipeline — GitHub Actions","#eef2f7","#9aa4b2"),
   (820,260,1140,620,"Google Kubernetes Engine + GPU pool (MIG)","#e9f3fe","#7badd6"),
   (850,300,520,260,"ns: model-serving  ·  the face-detection app","#fff5e6","#e0a86a"),
   (850,650,420,210,"ns: monitoring","#eafaf0","#86c9a8"),
   (1290,650,330,210,"ns: tracing","#f0eaf8","#b193d6"),
   (1640,300,300,560,"ns: logging (ELK)","#fdf0e6","#e0a86a")]

E=[("terraform","istio","provision GKE+GPU","#9aa4b2",1),("terraform","ansible","configure","#9aa4b2",1),
   ("dev","github","push code","#5b6472",0),("github","gha","trigger","#5b6472",0),
   ("gha","fdimage","build+test","#5b6472",0),("fdimage","registry","push image","#5b6472",0),
   ("registry","argocd","image","#5b6472",0),("argocd","kserve","deploy app","#5b6472",0),
   ("enduser","istio","request","#b8741a",0),("istio","kserve","route","#b8741a",0),
   ("kserve","triton","serve","#b8741a",0),("triton","yolo","inference","#1864ab",0),
   ("kserve","prom","metrics","#059669",1),("prom","grafana","visualize","#059669",0),
   ("kserve","otel","traces","#7c3aed",1),("otel","jaeger","","#7c3aed",0),
   ("kserve","filebeat","logs (collect)","#e0a86a",1),("filebeat","logstash","forward","#e0a86a",0),
   ("logstash","elastic","index","#e0a86a",0),("elastic","kibana","query","#e0a86a",0)]
build("00-app-architecture","App Architecture — Face Detection (CI/CD -> image -> GKE -> serve + observe)",2100,940,Z,N,E)
