import urllib.request, os, re, cairosvg
os.makedirs("/tmp/icons/png", exist_ok=True)
# tool: (simple-icons slug or None, brand hex, short label for fallback)
T = {
 "minio":("minio","#C72E49","MinIO"),
 "nvidia":("nvidia","#76B900","Triton"),
 "keycloak":("keycloak","#008AAA","Keycloak"),
 "ollama":("ollama","#0B0B0B","Ollama"),
 "weaviate":("weaviate","#3B82F6","Weaviate"),
 "typesense":("typesense","#D52B7C","Typesense"),
 "langfuse":("langfuse","#0EA5E9","Langfuse"),
 "debezium":("debezium","#C0392B","Debezium"),
 # niche / likely-missing -> fallback text logos
 "kserve":(None,"#2E7D9A","KServe"),
 "keda":(None,"#326CE5","KEDA"),
 "ragflow":(None,"#E8590C","RAGFlow"),
 "greatexpectations":(None,"#FF6310","Great Exp."),
 "katib":(None,"#1A73E8","Katib"),
 "oauth2proxy":(None,"#EF2D5E","OAuth2"),
 "evidently":(None,"#D7263D","Evidently"),
 "kubernetes":("kubernetes","#326CE5","K8s"),
}
def fallback(name,hexc,label):
    # rounded square with brand color + short label
    init=label.split()[0][:9]
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
<rect x="6" y="6" width="108" height="108" rx="22" fill="{hexc}"/>
<text x="60" y="68" font-family="Arial,Helvetica,sans-serif" font-size="{ 20 if len(init)<=6 else 16 }" font-weight="700" fill="#ffffff" text-anchor="middle">{init}</text></svg>'''
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"/tmp/icons/png/{name}.png", output_width=256, output_height=256)
    return "fallback"
def get(name,slug,hexc,label):
    if slug:
        try:
            url=f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg"
            raw=urllib.request.urlopen(url,timeout=15).read().decode()
            if "<path" in raw and "Couldn" not in raw:
                # inject brand fill on the path
                raw=re.sub(r"<svg ", f'<svg fill="{hexc}" ', raw,count=1)
                cairosvg.svg2png(bytestring=raw.encode(), write_to=f"/tmp/icons/png/{name}.png", output_width=256, output_height=256, background_color="white")
                return "downloaded"
        except Exception as e:
            pass
    return fallback(name,hexc,label)
for name,(slug,hexc,label) in T.items():
    r=get(name,slug,hexc,label)
    print(f"{name}: {r}")
