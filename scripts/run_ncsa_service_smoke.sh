#!/bin/bash
set -euo pipefail

floater_smoke_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$floater_smoke_root/scripts/conch_service_smoke.py" \
    --access-approved \
    --endpoint 'http://gpub055.delta.ncsa.illinois.edu:8000' \
    --tile-manifest "$floater_smoke_root/configs/ncsa_prad_service_smoke.csv" \
    --output "/work/nvme/bfqi/mhoda/conch-service-smoke-$(date -u +%Y%m%dT%H%M%SZ)"
