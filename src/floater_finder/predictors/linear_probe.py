"""Portable, pickle-free predictors. Inference requires only NumPy."""
from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np
from ..experiments import file_sha256
from ..scoring import pool
from .pooling import slide_vector


@dataclass(frozen=True)
class FrozenPredictor:
    spec: dict
    arrays: dict

    def __post_init__(self):
        s = self.spec
        if s.get('schema_version') != 1 or len(s.get('classes', [])) != 2 or len(set(s['classes'])) != 2:
            raise ValueError('Versioned binary predictor required')
        if s.get('kind') == 'linear_probe':
            d = s['input_dimensions'] * (3 if s['feature_rule'] == 'mean_max_topk' else 1)
            if (s['feature_rule'] not in ('mean', 'mean_max_topk') or
                any(self.arrays[k].shape != (d,) for k in ('coef', 'mean', 'scale')) or
                self.arrays['intercept'].shape != (1,) or (self.arrays['scale'] <= 0).any()):
                raise ValueError('Invalid linear probe dimensions/scales')
        elif s.get('kind') == 'zero_shot':
            if self.arrays['text'].shape != (2, s['input_dimensions']):
                raise ValueError('Text dimensions differ')
        else:
            raise ValueError('Unknown predictor kind')
        if any(not np.isfinite(v).all() for v in self.arrays.values()):
            raise ValueError('Nonfinite predictor parameters')

    def __call__(self, feats):
        x = np.asarray(feats)
        if x.ndim != 2 or not len(x) or x.shape[1] != self.spec['input_dimensions'] or not np.isfinite(x).all():
            raise ValueError('Nonempty finite features of the frozen dimension required')
        a, s = self.arrays, self.spec
        if s['kind'] == 'zero_shot':
            values = pool(np.einsum('id,cd->ic', x, a['text'], optimize=False), s['pooling'])
            margin = float(values[1]-values[0]); probability = None
        else:
            v = slide_vector(x, s['feature_rule'], s['top_k'])
            margin = float(((v-a['mean'])/a['scale']) @ a['coef'] + a['intercept'][0])
            values = np.array([-margin/2, margin/2])
            probability = float(np.exp(-np.logaddexp(0., -margin)))
        return dict(prediction=s['classes'][int(margin > 0)],
                    scores=dict(zip(s['classes'], map(float, values))), margin=margin,
                    positive_probability=probability,
                    probability_calibrated=False, model_id=s['model_id'])

    def score_slide(self, slide):
        if slide.metadata['model']['checkpoint_sha256'] != self.spec['checkpoint_sha256']:
            raise ValueError('Frozen predictor checkpoint differs from slide space')
        return self(slide.feats)

    def save(self, directory):
        path = Path(directory); path.mkdir(parents=True, exist_ok=False)
        with (path/'parameters.npz').open('xb') as f:
            np.savez_compressed(f, **self.arrays)
        from ..artifacts import write_json
        write_json(path/'predictor.json', dict(self.spec, parameters_sha256=file_sha256(path/'parameters.npz')))


def load_predictor(directory):
    path = Path(directory); s = json.loads((path/'predictor.json').read_text())
    if file_sha256(path/'parameters.npz') != s['parameters_sha256']:
        raise ValueError('Frozen predictor parameter hash differs')
    with np.load(path/'parameters.npz', allow_pickle=False) as data:
        arrays = {k: data[k] for k in data.files}
    return FrozenPredictor(s, arrays)
