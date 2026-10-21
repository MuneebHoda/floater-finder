#!/usr/bin/env python3
"""Propose outcome-blind, slide-disjoint metadata cohorts, without downloads."""
import argparse
import json

from floater_finder.validation_cohort import write_proposal

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train", required=True)
    p.add_argument("--catalog", required=True)
    p.add_argument("--exclude-manifest", required=True, action="append")
    p.add_argument("--output", required=True)
    p.add_argument("--per-group", type=int, default=20)
    p.add_argument("--seed", type=int, default=20261021)
    a = p.parse_args()
    print(json.dumps(write_proposal(a.train, a.catalog, a.exclude_manifest, a.output,
                                   per_group=a.per_group, seed=a.seed), indent=2))
