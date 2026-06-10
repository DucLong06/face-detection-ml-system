# Guide Phase 3 — Restructure Monorepo (tự làm, có test từng bước)

> Quy ước: mỗi step có **LỆNH** → **✅ TEST** (lệnh verify + kết quả mong đợi) → 🔥 nếu fail.
> Máy: đã có git/docker/python3.12. Làm tuần tự, commit theo nhóm như hướng dẫn.

## Step 0 — Đưa công việc hiện tại lên main trước
```bash
git push origin LongHD/NewPlans
# Mở PR LongHD/NewPlans → main trên GitHub, merge (squash hoặc merge tuỳ bạn)
git checkout main && git pull
```
✅ TEST: `git log --oneline -3` trên main thấy các commit diagrams (fcc361f, 09c8d07...).
🔥 Conflict với main cũ: main đã lâu không nhận code — resolve theo hướng giữ bản LongHD/NewPlans.

## Step 1 — Tạo branch restructure
```bash
git checkout -b restructure/monorepo-gitops
```
✅ TEST: `git branch --show-current` → `restructure/monorepo-gitops`.

## Step 2 — apps/: chuyển api/ → apps/face-detect/
```bash
mkdir -p apps/face-detect/src apps/face-detect/tests
git mv api/main.py api/my_yolo.py apps/face-detect/src/
git mv api/test_face_detection.py api/test.py apps/face-detect/tests/
git mv api/test_face.jpg apps/face-detect/tests/
git mv api/dockerfile apps/face-detect/Dockerfile
git mv api/README.md apps/face-detect/README.md
git mv api/docker-compose.yaml apps/face-detect/docker-compose.yaml
rm -rf api/__pycache__ && rmdir api
```
Sửa import/path trong code nếu có (`grep -rn "api/" apps/face-detect/` và sửa COPY path trong Dockerfile theo cấu trúc mới `src/`).
✅ TEST 1: `cd apps/face-detect && python3 -m pytest tests/ -x -q` → pass (hoặc cùng kết quả như trước khi chuyển — chạy thử trước ở Step 1 để có baseline).
✅ TEST 2: `docker build -t fd-test apps/face-detect/` → build OK.
✅ TEST 3: `git log --follow --oneline apps/face-detect/src/main.py | tail -1` → thấy commit cũ nhất (history giữ nguyên).
🔥 pytest import error: thêm `apps/face-detect/src/__init__.py` hoặc chạy với `PYTHONPATH=src`.
**Commit:** `git commit -m "refactor(apps): move api/ to apps/face-detect with src/tests layout"`

## Step 3 — charts/: đổi tên + values 2 profile
```bash
git mv charts/face-detection charts/face-detect
cp charts/face-detect/values.yaml charts/face-detect/values-cpu.yaml
printf '# GPU profile overrides (bật khi có GPU node)\n# nodeSelector: {gpu: "true"}\n# runtime: tensorrt\n' > charts/face-detect/values-gpu.yaml
git add charts/face-detect/values-*.yaml
```
✅ TEST: `helm lint charts/face-detect -f charts/face-detect/values-cpu.yaml` → `1 chart(s) linted, 0 chart(s) failed`.
✅ TEST: `helm template t charts/face-detect -f charts/face-detect/values-cpu.yaml | head -20` → render YAML hợp lệ.
**Commit:** `refactor(charts): rename face-detection to face-detect, add cpu/gpu values`

## Step 4 — gitops/ + clusters/ skeleton, chuyển infrastructure/
```bash
mkdir -p gitops/bootstrap gitops/apps gitops/platform/{platform,data,ml,serving,drift,rag,observability} clusters/kind
git mv charts/nginx-ingress gitops/platform/platform/nginx-ingress
git mv infrastructure clusters/gke
```
**QUAN TRỌNG — credentials:** `ls clusters/gke/credentials clusters/gke/ssh_key* 2>/dev/null` — nếu có file thật:
```bash
git ls-files clusters/gke | grep -iE "credential|ssh" || echo "KHONG TRACKED - OK"
mkdir -p ~/secure-backup && mv clusters/gke/credentials clusters/gke/ssh_key* ~/secure-backup/ 2>/dev/null
echo -e "clusters/gke/credentials/\nclusters/gke/ssh_key*\n" >> .gitignore
```
✅ TEST 1: `git ls-files | grep -iE "credential|ssh_key"` → rỗng (không file nhạy cảm tracked; nếu CÓ kết quả → DỪNG, báo lại — cần xử lý history riêng).
✅ TEST 2: `cd clusters/gke/terraform && terraform init -backend=false && terraform validate` → `Success!` (chỉ validate cú pháp, không cần GCP).
**Commit:** `refactor(infra): move infrastructure to clusters/gke, scaffold gitops tree`

## Step 5 — docs/: chuyển newplans → docs/architecture
```bash
git mv newplans docs/architecture
```
✅ TEST 1 (builders sống ở chỗ mới — dùng `__file__` nên tự theo):
```bash
cd docs/architecture/diagrams/icons && python3 prep_icons.py >/dev/null && python3 drilldown/prep_icons2.py >/dev/null && python3 rebuild_icons.py | tail -1 && python3 overview_builder.py && cd -
```
→ `01-overview written`.
✅ TEST 2 (link check):
```bash
python3 - <<'EOF'
import re, os
for md in ["docs/architecture/README.md", "README.md"]:
    if not os.path.exists(md): continue
    base = os.path.dirname(md)
    links = re.findall(r'\]\(([^)#:]+?)\)', open(md).read())
    bad = [l for l in links if l and not l.startswith("http") and not os.path.exists(os.path.join(base, l))]
    print(md, "->", bad or "OK")
EOF
```
→ tất cả `OK`. 🔥 Link gãy: phần lớn do path `newplans/` cũ — sửa trong file md tương ứng.
**Commit:** `refactor(docs): move newplans to docs/architecture`

## Step 6 — Dọn rác + trích values monitoring cũ
```bash
mkdir -p gitops/platform/observability/_legacy-values
# trích values bạn từng tune (xem nhanh từng cái, cái nào default thì bỏ):
git mv monitoring/K8s/kube-prometheus-stack/values.yaml gitops/platform/observability/_legacy-values/kube-prometheus-stack-values.yaml 2>/dev/null || true
# (lặp tương tự cho elk/jaeger nếu có values.yaml tự sửa)
git rm -r monitoring custom_images models scripts notebooks 2>/dev/null
git rm repomix-output.xml
echo "repomix-output*.xml" >> .gitignore
# NEWREADME.md / newreview.md: đọc lướt, phần còn giá trị copy vào docs/architecture/, rồi xoá
rm -f NEWREADME.md newreview.md
git rm -r datapipeline 2>/dev/null; mkdir -p pipelines && git mv datapipeline pipelines/_legacy-datapipeline 2>/dev/null || true
```
✅ TEST: `du -sh .git/.. --exclude=.git` giảm ~18MB+; `git status` không còn file rác untracked.
**Commit:** `chore: remove vendored charts, stale files, 18MB repomix dump`

## Step 7 — README skeleton (root + 6 con)
Tạo `README.md` (root — viết lại): hình `docs/architecture/diagrams/icons/01-overview.png` + bảng 7 domain status ⬜ + link 6 README con + quickstart (trỏ phase 5).
Tạo skeleton 6 file: `apps/README.md`, `charts/README.md`, `gitops/README.md`, `clusters/README.md`, `pipelines/README.md`, `docs/README.md` — mỗi cái 5-10 dòng: mục đích, cấu trúc, "đọc gì tiếp".
✅ TEST: chạy lại link-check Step 5 TEST 2 cho root README → OK; mở GitHub preview soát hình hiển thị.
**Commit:** `docs: root README architecture hub + per-directory README skeletons`

## Step 8 — PR
```bash
git push -u origin restructure/monorepo-gitops
gh pr create --base main --title "refactor: monorepo GitOps tree" --body "Tree per plan 260611. No runtime changes."
```
✅ TEST (Definition of Done):
- [ ] `tree -L 2 -d` khớp Target Tree trong plan.md
- [ ] pytest + docker build + helm lint + terraform validate đều xanh (Steps 2-4)
- [ ] Link check OK, builders render OK (Step 5)
- [ ] `git ls-files | grep -iE "credential|ssh_key"` rỗng
- [ ] PR merge vào main

## 📚 Học trong phase này
`git mv` + `--follow` history · Helm chart anatomy (Chart.yaml/values/templates) · terraform validate offline.
