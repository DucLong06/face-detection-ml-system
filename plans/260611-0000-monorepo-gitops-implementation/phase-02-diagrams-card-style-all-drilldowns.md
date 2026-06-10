---
phase: 2
title: "Diagrams: card style 7 drilldown + apply findings"
status: completed
priority: P2
effort: "4h"
dependencies: [1]
---

# Phase 2: Card Style cho 7 Drilldown + Áp Findings

## Overview
> **260611 progress:** phần STYLE đã làm xong trước theo yêu cầu user (7 drilldown card-style, autofit zones, vision review 7/7 PASS, drawio verified). Phần còn lại của phase = áp content findings từ red-team phase 1 (re-render rẻ).

Đồng bộ 8 hình về card style (engine sẵn từ plan 260610-1130) + sửa nội dung hình theo findings phase 1 đã được duyệt.

## Requirements
- Functional: 7 drilldown bật `cards/badges/zone_header/corner_r` + re-space grid card 116×92 per zone; nội dung node/edge sửa theo adjudicated findings (nếu có).
- Non-functional: pass vision checklist cũ (0 edge xuyên card, 0 label đè, arrowhead dính node); drawio waypoints + flowAnimation giữ.

## Related Code Files
- Modify: `newplans/diagrams/icons/drilldown/drilldowns.py` (bật flags + re-space coords từng zone)
- Modify (nếu findings đổi stack): `newplans/diagrams/icons/overview_builder.py`
- Overwrite: `drilldown/zone-1..7-*.{png,svg,drawio}`

## Implementation Steps
1. Icons check `/tmp/icons/png` (chạy lại prep nếu /tmp wipe — REGENERATE.md).
2. Re-space từng zone theo pitch 116 (cách làm y hệt overview: bảng y-row cũ→mới); zone-1 (22 edge) và zone-6 (19 edge) làm sau cùng — khó nhất.
3. Áp findings phase 1 vào node/edge data (cả overview nếu dính).
4. Render → vision review (subagent 1400px-copy protocol nếu context image đầy) → fix → lặp; cap 3 vòng/hình.
5. Verify drawio 7 file (XML valid, edges == waypointed, anim đúng) + invariance overview nếu không sửa nội dung.

## Success Criteria
- [ ] 7/7 PNG pass checklist, style đồng bộ overview
- [ ] drawio 7/7 valid + animated
- [ ] Findings được phản ánh đúng trong hình (đối chiếu bảng adjudication)
- [ ] README captions cập nhật nếu hình đổi nội dung

## Risk Assessment
- Re-space 7 zone tốn vòng lặp → engine đã có via/rail_y xử corridor chật; budget 3 vòng/hình, escalate phần dư.
