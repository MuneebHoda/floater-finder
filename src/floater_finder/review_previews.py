"""Geometry-selected galleries of unchanged saved PNGs, never inferred tissue boundaries."""
from copy import deepcopy
import hashlib
from html import escape
import io
import math
from pathlib import Path
import re
from PIL import Image

from .review_report import render_html


def select_examples(indices, coordinates):
    """Up to four evenly spaced positions in x/y/index order; no scores or labels."""
    order = sorted(indices, key=lambda i:(*coordinates[i], i))
    k = min(4, len(order))
    return [order[j*(len(order)-1)//(k-1)] for j in range(k)] if k > 1 else order


def attach_previews(report, rows, metadata, png_hashes, directory, asset_directory, maximum_new_bytes):
    """Copy only selected PNGs byte-for-byte; each unique source opens once per slide."""
    sid = report['host_id']; directory = Path(directory).resolve(); asset_directory = Path(asset_directory)
    n = len(rows); field = metadata['tile_size']; pixels = metadata['export_pixels']
    if (not re.fullmatch('[a-f0-9]{32}', sid) or n != report['tile_count'] or not 1 <= n <= 1024 or
            metadata['slide_id'] != sid or metadata['source_kind'] != report['source_kind'] or
            metadata['cohort_split'] != 'train' or metadata['coordinate_units'] != 'microns' or
            metadata['coordinate_reference'] != 'tile_top_left' or metadata['microns_per_unit'] != 1 or
            len(field) != 2 or any(not math.isfinite(v) or v <= 0 for v in field) or
            type(pixels) is not int or not 1 <= pixels <= 512 or maximum_new_bytes < 0):
        raise ValueError('Bounded aligned training PNGs and recorded physical geometry required')
    coordinates = [(float(r['x']), float(r['y'])) for r in rows]
    if (len({r['tile_id'] for r in rows}) != n or set(png_hashes) != {r['tile_id'] for r in rows} or
            any(r['image_id'] != sid or not math.isclose(float(r['area_mm2']), field[0]*field[1]/1e6, rel_tol=1e-9, abs_tol=1e-12) for r in rows) or
            any(not math.isfinite(v) or v < 0 for xy in coordinates for v in xy)):
        raise ValueError('Saved tile order, physical scale or PNG identity differs')
    mapped = set()
    for p in report['components']:
        ix = p['tile_indices']
        if (not ix or len(ix) != p['tile_count'] or len(set(ix)) != len(ix) or mapped.intersection(ix) or
                any(type(i) is not int or not 0 <= i < n for i in ix) or
                not math.isclose(p['occupied_tile_area_mm2'], len(ix)*field[0]*field[1]/1e6, rel_tol=1e-9, abs_tol=1e-12)):
            raise ValueError('Original disjoint component membership/footprint required')
        mapped.update(ix)
    assets = {}; cache = {}; copied_bytes = 0

    def tile(index):
        nonlocal copied_bytes
        if index in cache: return deepcopy(cache[index])
        row = rows[index]; source = directory/row['path']
        if (Path(row['path']).name != row['path'] or source.resolve().parent != directory or
                source.suffix != '.png' or not source.is_file()):
            raise ValueError('PNG must stay inside its verified slide directory')
        with source.open('rb') as handle: payload = handle.read(1024*1024+1)
        digest = hashlib.sha256(payload).hexdigest()
        if len(payload) > 1024*1024 or digest != png_hashes[row['tile_id']]:
            raise ValueError('Selected source PNG checksum/byte bound differs')
        with Image.open(io.BytesIO(payload)) as image:
            if image.format != 'PNG' or image.mode != 'RGB' or image.size != (pixels, pixels):
                raise ValueError('PNG format/shape differs from recorded export pixels')
            image.load()
        if copied_bytes+len(payload) > maximum_new_bytes:
            raise ValueError('Frozen copied-PNG byte budget exceeded')
        name = sid+f'-t{index:04d}.png'; asset_path = 'tiles/'+name
        with (asset_directory/name).open('xb') as handle: handle.write(payload)
        copied_bytes += len(payload)
        assets[asset_path] = dict(sha256=digest, bytes=len(payload), source_path=str(source.resolve()))
        record = dict(tile_index=index, source_tile_id=row['tile_id'], source_png_sha256=digest,
            asset_path=asset_path, x_um=coordinates[index][0], y_um=coordinates[index][1],
            field_um_xy=list(field), source_pixels_xy=[pixels,pixels],
            rgb_assignment='mapped_proxy' if index in mapped else 'unknown')
        cache[index] = record; return deepcopy(record)

    result = deepcopy(report)
    for p in result['components']:
        inside = set(p['tile_indices']); outside = set(range(n))-inside
        p['previews'] = dict(component=[tile(i) for i in select_examples(inside,coordinates)],
            outside=[tile(i) for i in select_examples(outside,coordinates)],
            available_component_tiles=len(inside), available_outside_tiles=len(outside))
    result['category'] = 'review_only_dependence_with_previews'
    result['preview_policy'] = dict(examples_per_panel=4, selection='evenly spaced x/y/index order',
        source_pixels='unchanged PNG byte copies', spatial_reconstruction=False, selection_uses_labels_or_scores=False)
    result['limitations'] = [v for v in result['limitations'] if not v.startswith('No image panels')]
    result['limitations'].append('Galleries are selected saved tile examples, not a spatial reconstruction or complete tissue inspection; no calibrated policy or tissue exclusion.')
    return result, assets


def render_preview_html(report):
    page = render_html(report); sections = page.split('</summary>')
    if len(sections) != len(report['components'])+1:
        raise ValueError('Frozen base renderer component structure changed')
    panels = []
    for p in report['components']:
        body = '<p>Separate saved tile examples, not a spatial reconstruction. These display subsets do not change the saved score context.</p>'
        for role, title in [('component','Component'),('outside','Outside component')]:
            preview = p['previews']; available = preview['available_'+role+'_tiles']
            body += '<h3>'+title+' — '+str(len(preview[role]))+' of '+str(available)+' saved tiles</h3><div class="tile-gallery">'
            for t in preview[role]:
                if not re.fullmatch(r'tiles/[a-f0-9]{32}-t[0-9]{4}\.png', t['asset_path']):
                    raise ValueError('Safe local preview asset required')
                caption = (f"Tile {t['tile_index']}; x={t['x_um']:.3f}, y={t['y_um']:.3f} µm; "
                    f"field {t['field_um_xy'][0]:.3f} × {t['field_um_xy'][1]:.3f} µm. "
                    + ('RGB assignment unknown.' if t['rgb_assignment']=='unknown' else 'RGB proxy assignment.'))
                body += '<figure><img loading="lazy" width="224" height="224" src="../'+escape(t['asset_path'])+'" alt="'+escape(caption)+'"><figcaption>'+escape(caption)+'</figcaption></figure>'
            if not preview[role]: body += '<p>No saved outside tiles; empty exclusion remains unevaluable.</p>'
            body += '</div>'
        panels.append(body)
    body = ''.join(sections[i]+'</summary>'+panels[i] for i in range(len(panels)))+sections[-1]
    return body.replace('</style>', '.tile-gallery{display:flex;flex-wrap:wrap;gap:1rem}.tile-gallery figure{width:180px;margin:0}.tile-gallery img{width:180px;max-width:100%;height:auto}.tile-gallery figcaption{font-size:.8rem;overflow-wrap:anywhere}</style>', 1)
