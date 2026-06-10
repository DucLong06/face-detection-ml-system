# Guide Phase 4 — CI GitHub Actions (tự làm, có test từng bước)

> Tiền đề: phase 3 đã merge main. Registry đã chốt: **GHCR** `ghcr.io/duclong06/face-detect`.
> Branch làm việc: `git checkout main && git pull && git checkout -b ci/github-actions`

## Step 1 — Soát test trước khi đưa vào CI
```bash
cd apps/face-detect && python3 -m pytest tests/ -v
```
Phân loại: test nào cần model weights/server đang chạy → đánh marker:
```python
# trong test file:  @pytest.mark.integration
```
Tạo `apps/face-detect/pytest.ini`:
```ini
[pytest]
markers =
    integration: needs running server or model weights (skipped in CI)
```
✅ TEST: `python3 -m pytest tests/ -m "not integration" -q` → pass, 0 errors (đây chính là lệnh CI sẽ chạy — KHÔNG dùng `|| true` để lờ test fail).

## Step 2 — Workflow CI app (file đầy đủ, copy rồi đọc hiểu từng khối)
Tạo `.github/workflows/app-ci.yaml`:
```yaml
name: app-ci
on:
  pull_request:
    paths: ["apps/**", "charts/face-detect/**"]
  push:
    branches: [main]
    paths: ["apps/**"]

concurrency: { group: gitops-bump, cancel-in-progress: false }   # S2: 2 push gần nhau không đua bump

env:
  IMAGE: ghcr.io/duclong06/face-detect

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip }
      - run: pip install -r requirements.txt pytest
      - run: cd apps/face-detect && pytest tests/ -m "not integration" -q

  build-push:
    if: github.event_name == 'push'      # chỉ build trên main
    needs: test
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: "${{ github.actor }}", password: "${{ secrets.GITHUB_TOKEN }}" }
      - uses: docker/build-push-action@v6
        with:
          context: apps/face-detect
          push: true
          tags: |
            ${{ env.IMAGE }}:sha-${{ github.sha }}
            ${{ env.IMAGE }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  bump-tag:
    needs: build-push
    runs-on: ubuntu-latest
    permissions: { contents: write }
    steps:
      - uses: actions/checkout@v4
      - name: bump image tag in values-cpu (GitOps handoff -> ArgoCD)
        run: |
          yq -i '.image.tag = "sha-${{ github.sha }}"' charts/face-detect/values-cpu.yaml
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git commit -am "ci: bump face-detect image to sha-${{ github.sha }} [skip ci]"
          for i in 1 2 3; do git push && break; git pull --rebase origin main; done   # S2: retry chống non-fast-forward
```
Kiểm tra key `image.tag` tồn tại trong `values-cpu.yaml` (sửa values cho khớp: `image: {repository: ghcr.io/duclong06/face-detect, tag: "latest"}`).
✅ TEST (cú pháp, local): `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/app-ci.yaml'))" && echo YAML-OK`.

## Step 3 — Workflow lint charts
Tạo `.github/workflows/lint-charts.yaml`:
```yaml
name: lint-charts
on:
  pull_request:
    paths: ["charts/**", "gitops/**"]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-helm@v4
      - run: |
          for c in charts/*/; do
            helm lint "$c" -f "$c/values-cpu.yaml" || exit 1
            helm template t "$c" -f "$c/values-cpu.yaml" > /dev/null
          done
```
✅ TEST local trước: chạy đúng vòng for đó trong terminal → exit 0.

## Step 4 — Push PR và xem CI chạy thật
```bash
git add .github apps/face-detect/pytest.ini charts/face-detect/values-cpu.yaml
git commit -m "ci: github actions app pipeline (test/build/push/bump) + chart lint"
git push -u origin ci/github-actions
gh pr create --base main --title "ci: GitHub Actions thay Jenkins" --body "GHCR + GitOps tag bump"
gh pr checks --watch
```
✅ TEST: cả 2 workflow xanh trên PR (job `test` + `lint`; `build-push` không chạy trên PR — đúng thiết kế).
🔥 pip install fail: requirements.txt ở root — đường dẫn đúng vì checkout root; nếu app có req riêng thì trỏ `apps/face-detect/requirements.txt`.

## Step 5 — Merge và verify đoạn main
Merge PR →
✅ TEST 1: `gh run list --workflow=app-ci --limit 1` → run mới trên main: cả 3 job xanh.
✅ TEST 2 (image public để kind pull): GitHub → Packages → face-detect → Package settings → **Change visibility = Public**. Rồi:
```bash
docker logout ghcr.io && docker pull ghcr.io/duclong06/face-detect:latest
```
→ pull được KHÔNG cần login.
✅ TEST 3b (S2 race): push 2 commit cách nhau ~30s → cả 2 run xanh, values có tag của commit sau cùng, không run nào đỏ vì push rejected.
✅ TEST 3 (bump hoạt động, không loop): `git pull && git log --oneline -2` → thấy commit `ci: bump face-detect image to sha-... [skip ci]`; `gh run list --limit 3` → KHÔNG có run mới do commit bump (nhờ `[skip ci]` + paths filter).
✅ TEST 4: `yq '.image.tag' charts/face-detect/values-cpu.yaml` → `sha-<sha mới nhất>`.

## Step 6 — Khai tử Jenkins
```bash
git checkout -b ci/remove-jenkins && git rm Jenkinsfile
echo "- $(date +%F): CI migrated Jenkins -> GitHub Actions (GHCR, GitOps tag bump)" >> docs/changelog.md
git commit -am "ci: remove Jenkinsfile (replaced by GitHub Actions)" && git push -u origin ci/remove-jenkins && gh pr create --fill
```
✅ TEST (Definition of Done):
- [ ] Push code app → image mới trên GHCR + values bump tự động, không vòng lặp CI
- [ ] PR bất kỳ sửa chart → lint chạy
- [ ] `docker pull` ẩn danh OK (package public)
- [ ] Jenkinsfile đã xoá, changelog ghi nhận
- [ ] Cập nhật root README mục CI/CD (1 đoạn + link workflow)

## 📚 Học trong phase này
GHA: events/paths filter/needs/permissions · GITHUB_TOKEN vs PAT · buildx cache `type=gha` · yq · vì sao bump-tag = GitOps handoff (CI không deploy, chỉ ghi mong muốn vào git).
