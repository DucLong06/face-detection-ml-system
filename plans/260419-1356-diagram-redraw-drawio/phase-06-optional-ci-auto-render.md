---
phase: 06
title: Optional CI auto-render drawio→png
status: optional
priority: P3
effort: ~2h
blockedBy: [05]
---

# Phase 06 — Optional CI Auto-Render

## Context Links
- Plan: [../plan.md](./plan.md)
- Tool: `jgraph/drawio-export` Docker image

## Overview
- **Priority**: P3 (optional, quality-of-life)
- **Status**: optional (skip nếu workflow manual export OK)
- **Description**: GitHub Action auto-render `.drawio` → `.png` mỗi khi push. Bỏ step manual export PNG.

## Key Insights
- Trade-off: CI render = lose local preview control, gain auto-sync. Manual = control style review trước commit, chấp nhận export step.
- Skip nếu user vẽ không thường xuyên (1 batch coursework xong là thôi).

## Requirements

### Functional
- GitHub Action trigger on push to `main` hoặc PR touching `docs/diagrams/*.drawio`.
- Render mọi `.drawio` → `.png` 1920px scale 2x white background.
- Commit/push kết quả PNG (hoặc fail check nếu PNG lệch từ `.drawio`).

### Non-Functional
- Build time ≤3 phút.
- Không require secrets (public Docker image).

## Architecture

```yaml
# .github/workflows/drawio-render.yml
name: Render drawio to PNG
on:
  push:
    paths: ['docs/diagrams/**.drawio']
  pull_request:
    paths: ['docs/diagrams/**.drawio']
jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Render
        uses: docker://jgraph/drawio-export:latest
        with:
          args: --format png --scale 2 --border 10 /data/docs/diagrams
      - name: Commit rendered PNGs
        run: |
          git config user.name "drawio-bot"
          git config user.email "bot@face-detect"
          git add docs/diagrams/*.png
          git diff --cached --quiet || git commit -m "ci(diagrams): auto-render PNG from drawio"
          git push
```

## Related Code Files

**Create**:
- `.github/workflows/drawio-render.yml`

## Implementation Steps

1. Research `jgraph/drawio-export` CLI flags (link: `https://github.com/jgraph/drawio-export`).
2. Tạo workflow file theo template trên.
3. Test local bằng `act` (GitHub Actions runner local).
4. Push branch, verify trigger.
5. Verify PNG output match manual export từ Phase 02–04.
6. Merge.

## Todo List

- [ ] Quyết định có làm Phase này không
- [ ] Tạo `.github/workflows/drawio-render.yml`
- [ ] Test local với `act`
- [ ] Push test branch
- [ ] Verify PNG quality khớp manual export
- [ ] Document trong `docs/diagrams/README.md`: "PNG auto-rendered by CI, do not edit manually"

## Success Criteria
- [ ] Workflow trigger khi edit `.drawio`
- [ ] PNG output match manual (±5% file size)
- [ ] Build ≤3 phút
- [ ] No secrets required

## Risk Assessment

| Risk | Mitigation |
|---|---|
| `jgraph/drawio-export` output style lệch từ desktop Draw.io | Test 1 diagram first, compare pixel-by-pixel. Adjust flags if needed |
| CI commit loop (push triggers re-run) | Path filter `paths:` + skip PNG-only changes in trigger |
| Permission: bot cannot push to main | Configure PAT hoặc use `peter-evans/create-pull-request` action |

## Security Considerations
- Bot credentials via `GITHUB_TOKEN` (default, restricted to repo scope).
- No external secrets needed.

## Next Steps
→ Plan done. Archive via `/ck:plan archive` khi hoàn tất.
