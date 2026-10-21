#!/usr/bin/env python3
"""Reproduce descriptive v2 figures from completed saved-measurement analysis; no model execution."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--results', type=Path, required=True)
p.add_argument('--components', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
r = json.loads(a.results.read_text()); rows = json.loads(a.components.read_text())
if a.output.exists():
    raise FileExistsError('Preserve prior figures')
a.output.mkdir(parents=True)
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': 'white', 'savefig.facecolor': 'white'})
labels = {'visual_rank': 'Visual', 'decision_rank': 'Absolute margin influence', 'spatial_rank': 'Spatial', 'visual_relevance_rank': 'Visual + relevance', 'combined_rank': 'Combined average'}
colors = dict(zip(labels, ['#1c7894', '#bd4c44', '#8b6bb1', '#ce8a29', '#299471']))


def save(fig, name):
    for extension in ('png', 'svg'):
        fig.savefig(a.output / (name + '.' + extension), dpi=180, bbox_inches='tight')
    plt.close(fig)


fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
for name, method in r['methods'].items():
    m = method['splits']['calibration']['metrics']; top = method['top_one_unbudgeted']['calibration']['metrics']
    axes[0].scatter(100 * m['unmodified_alert_rate'], 100 * m['fragment_recall'], color=colors[name], s=70, label=labels[name])
    axes[0].scatter(100 * top['unmodified_alert_rate'], 100 * top['fragment_recall'], facecolors='none', edgecolors=colors[name], s=70)
    axes[0].plot([100 * m['unmodified_alert_rate'], 100 * top['unmodified_alert_rate']], [100 * m['fragment_recall'], 100 * top['fragment_recall']], color=colors[name], alpha=.45, linestyle=':')
    axes[1].scatter(m['mean_components_per_unmodified_slide'], 100 * m['clean_damage_rate'], color=colors[name], s=70)
    axes[1].scatter(top['mean_components_per_unmodified_slide'], 100 * top['clean_damage_rate'], facecolors='none', edgecolors=colors[name], s=70)
axes[0].axvspan(0, 10, alpha=.08, color='#299471'); axes[0].axvline(10, color='#299471', linestyle='--', linewidth=1)
axes[0].axhline(20, color='#555555', linestyle='--', linewidth=1)
axes[0].set(xlabel='Unmodified slides offered review (%)', ylabel='Injected fragments with any tile flagged (%)', xlim=(-3, 104), ylim=(-3, 104), title='Known calibration: recall versus alert burden')
axes[0].legend(loc='upper left', fontsize=8)
axes[1].axvline(.5, color='#299471', linestyle='--', linewidth=1); axes[1].axhline(5, color='#555555', linestyle='--', linewidth=1)
axes[1].set(xlabel='Components flagged per unmodified slide', ylabel='Originally correct clean predictions damaged (%)', title='Hypothetical filtering harm; no tissue removed')
fig.suptitle('Ranked review v2: filled = train-selected; hollow = unbudgeted top one', fontsize=13)
fig.text(.5, -.03, '24 unmodified calibration slides; 40 mixtures across 8 reused hosts. Calibration is iterative development, not independent validation.', ha='center', fontsize=9)
fig.tight_layout(); save(fig, 'ranked_review_tradeoff')

cal = [v for v in rows if v['split'] == 'calibration']
groups = [([v for v in cal if v['kind'] == 'unmodified' and v['genuine_annotated_cancer']], 'Native annotated cancer'),
          ([v for v in cal if v['category'] == 'synthetic_foreign_pure'], 'Donor-only mapped tiles'),
          ([v for v in cal if v['category'] == 'synthetic_mixed'], 'Donor + native co-mapped')]
fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
for ax, key, title in zip(axes, ['visual', 'influence', 'area_mm2'], ['Visual anomaly', 'Signed cancer-margin influence', 'Observed area (mm²)']):
    data = [[v[key] for v in values if v[key] is not None] for values, _ in groups]
    nonempty = [(i, d) for i, d in enumerate(data) if d]
    if nonempty:
        ax.boxplot([d for i, d in nonempty], positions=[i + 1 for i, d in nonempty], widths=.55, showfliers=True,
                   medianprops={'color': '#bd4c44'}, flierprops={'markersize': 3})
    ax.set_xticks(range(1, 4), [f'{label}\nn={len(values)} components' for values, label in groups], rotation=20, ha='right', fontsize=8)
    ax.set_title(title)
    if key == 'influence':
        ax.axhline(0, color='#888888', linewidth=1); ax.axhline(.01, color='#bd4c44', linestyle='--', linewidth=1)
    if key == 'visual':
        ax.axhline(.24603846669197083, color='#bd4c44', linestyle='--', linewidth=1)
    if key == 'area_mm2':
        ax.set_yscale('log')
fig.suptitle('Existing component signals do not establish foreignness', fontsize=13)
fig.text(.5, -.04, 'Descriptive component observations; injected components recur across nested doses. Dashed lines are rejected v1 thresholds.', ha='center', fontsize=9)
fig.tight_layout(); save(fig, 'signal_distributions')

fig, ax = plt.subplots(figsize=(9.5, 4.6))
d = r['failure_decomposition']['splits']['calibration']
keys = ['v1_foreign_visual_pass', 'v1_foreign_influence_pass', 'v1_foreign_spatial_pass', 'v1_foreign_visual_and_influence', 'v1_foreign_all_pass']
values = [d[k] for k in keys]
ax.barh(['Visual alone', 'Signed influence alone', 'Area/isolation alone', 'Visual AND influence', 'All v1 requirements'], values, color=['#1c7894', '#bd4c44', '#8b6bb1', '#ce8a29', '#299471'])
for i, value in enumerate(values):
    ax.text(value + .5, i, f'{value}/{d["positive_trials"]}', va='center')
ax.invert_yaxis(); ax.set(xlim=(0, d['positive_trials'] + 5), xlabel='Mixtures with a donor-bearing component passing each condition', title='Why v1 failed: signal requirements do not coincide')
fig.text(.5, -.015, 'Same saved 40 calibration mixtures; no rerun. A component can be consequential without being foreign.', ha='center', fontsize=9)
fig.tight_layout(); save(fig, 'v1_failure_intersections')
provenance = dict(source_commit=r['source_commit'], config_sha256=r['config_sha256'], measurements_sha256=r['component_cases_sha256'],
    result_sha256=hashlib.sha256(a.results.read_bytes()).hexdigest(), component_diagnostics_sha256=hashlib.sha256(a.components.read_bytes()).hexdigest(),
    final_test_slides_scored=False, calibration_role=r['calibration_role'], figures={f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in a.output.iterdir()})
(a.output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
