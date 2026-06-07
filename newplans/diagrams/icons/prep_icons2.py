import urllib.request, os, re, cairosvg
os.makedirs("/tmp/icons/png", exist_ok=True)
# name: (simple-icons slug or None, brand hex, fallback label)
T = {
 "iceberg":("apacheiceberg","#4A90D9","Iceberg"),
 "lakefs":("lakefs","#14B8A6","lakeFS"),
 "qdrant":("qdrant","#DC244C","Qdrant"),
 "opentelemetry":("opentelemetry","#425CC7","OTel"),
 "argo":("argo","#EF7B4D","Argo"),
 "knative":("knative","#0865AD","Knative"),
 "ray":("ray","#028CF0","Ray"),
 "vllm":(None,"#30A2FF","vLLM"),
 "feast":(None,"#1565C0","Feast"),
 "kyverno":(None,"#1A73E8","Kyverno"),
 "openmetadata":(None,"#0968DA","OpenMeta"),
 "guardrails":(None,"#76B900","Guardrails"),
 "alibidetect":(None,"#F39200","Alibi Detect"),
 "iter8":(None,"#6A1B9A","Iter8"),
 "kafkaconnect":(None,"#231F20","Kafka Connect"),
 "schemaregistry":(None,"#0B5FFF","Schema Reg"),
}
def fallback(name,hexc,label):
    init=label.split()[0][:9]
    fs = 20 if len(init)<=6 else (16 if len(init)<=8 else 14)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><rect x="6" y="6" width="108" height="108" rx="22" fill="{hexc}"/><text x="60" y="68" font-family="Arial,Helvetica,sans-serif" font-size="{fs}" font-weight="700" fill="#ffffff" text-anchor="middle">{init}</text></svg>'
    cairosvg.svg2png(bytestring=svg.encode(),write_to=f"/tmp/icons/png/{name}.png",output_width=256,output_height=256)
    return "fallback"
def get(name,slug,hexc,label):
    if slug:
        try:
            raw=urllib.request.urlopen(f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg",timeout=15).read().decode()
            if "<path" in raw and "Couldn" not in raw:
                raw=re.sub(r"<svg ",f'<svg fill="{hexc}" ',raw,count=1)
                cairosvg.svg2png(bytestring=raw.encode(),write_to=f"/tmp/icons/png/{name}.png",output_width=256,output_height=256,background_color="white")
                return "downloaded"
        except Exception: pass
    return fallback(name,hexc,label)
for n,(s,h,l) in T.items():
    print(f"{n}: {get(n,s,h,l)}")
