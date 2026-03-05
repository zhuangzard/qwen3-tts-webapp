#!/usr/bin/env bash
set -euo pipefail

# One-command figure reproduction for DPC-GNN-RL paper assets.
# - Copies canonical figures into docs/paper_assets/figures
# - Normalizes PNG metadata to 300 DPI
# - Verifies naming and file presence

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$REPO_ROOT/docs/paper_assets/figures"

CANONICAL=(
  "multi_instrument_perf.png"
  "reward_curve.png"
  "gradient_norm.png"
)

mkdir -p "$OUT_DIR"

python3 - "$REPO_ROOT" "$OUT_DIR" "${CANONICAL[@]}" <<'PY'
import os
import sys
from pathlib import Path

repo = Path(sys.argv[1])
out = Path(sys.argv[2])
canonical = sys.argv[3:]

try:
    from PIL import Image
except Exception as e:
    raise SystemExit(f"[ERR] Pillow is required: pip install pillow ({e})")

print("[INFO] Reproducing paper figures...")
missing = []
for name in canonical:
    src = repo / name
    if not src.exists():
        missing.append(name)
        continue

if missing:
    raise SystemExit("[ERR] Missing source figure(s): " + ", ".join(missing))

for name in canonical:
    src = repo / name
    dst = out / name
    with Image.open(src) as im:
        # Re-save with explicit 300 DPI to ensure print-ready metadata.
        im.save(dst, dpi=(300, 300), optimize=True)

print(f"[OK] Wrote {len(canonical)} figure(s) to {out}")

# Validate naming consistency + dpi
expected = set(canonical)
actual = {p.name for p in out.glob('*.png')}
extra = sorted(actual - expected)
miss = sorted(expected - actual)
if miss or extra:
    msg = []
    if miss:
        msg.append("missing=" + ",".join(miss))
    if extra:
        msg.append("extra=" + ",".join(extra))
    raise SystemExit("[ERR] Naming mismatch: " + " ; ".join(msg))

for name in canonical:
    p = out / name
    with Image.open(p) as im:
        dpi = im.info.get('dpi', (0, 0))
        dx, dy = float(dpi[0]), float(dpi[1])
        if dx < 299.0 or dy < 299.0:
            raise SystemExit(f"[ERR] DPI check failed for {name}: {dpi}")
        print(f"[OK] {name}: size={im.size}, dpi={dpi}")

print("[DONE] Figure reproduction + validation complete.")
PY
