"""Training-only grouped nested CV, with every attempted regularization fit recorded."""
import warnings
import numpy as np
from ..panda_final import classification_summary
from .linear_probe import FrozenPredictor
from .pooling import slide_vector


def metrics(rows, classes, seed):
    truth = [classes.index(r['truth']) for r in rows]
    predictions = [classes.index(r['prediction']) for r in rows]
    result = classification_summary(truth, predictions, seed=seed, repetitions=2000)
    result['classes'] = list(classes)
    p = [r['positive_probability'] for r in rows]
    if all(v is not None for v in p):
        y = np.array([r['truth'] == classes[1] for r in rows]); p = np.array(p)
        bins = np.minimum((p*5).astype(int), 4)
        result.update(brier=float(np.mean((p-y)**2)),
                      ece_five_fixed_probability_bins=float(sum(np.mean(bins==b)*abs(p[bins==b].mean()-y[bins==b].mean()) for b in range(5) if (bins==b).any())),
                      probability_caveat='Uncalibrated balanced logistic outputs; class weighting changes class prior. No Platt/isotonic fitting.')
    else:
        result.update(brier=None, probability_caveat='Cosine similarities are not probabilities; no arbitrary temperature fitted.')
    result['independent_unit'] = 'Unique slide; unknown patient identities prevent verified patient independence'
    return result


def grouped_folds(y, groups, n_splits, seed):
    from sklearn.model_selection import StratifiedGroupKFold
    folds = list(StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(np.zeros(len(y)), y, groups))
    for train, valid in folds:
        if set(groups[train]) & set(groups[valid]) or len(set(y[train])) != 2 or len(set(y[valid])) != 2:
            raise ValueError('Every CV fold must have disjoint groups and both classes')
    return folds


def fit_linear(x, y, c, config):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.exceptions import ConvergenceWarning
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        estimator = make_pipeline(StandardScaler(), LogisticRegression(C=c, class_weight='balanced',
            solver='liblinear', max_iter=config['maximum_iterations'], tol=config['tolerance'],
            random_state=config['seed']))
        estimator.fit(x, y)
    messages = [str(w.message) for w in caught]
    if any(issubclass(w.category, ConvergenceWarning) for w in caught):
        raise RuntimeError('Convergence failure: '+'; '.join(messages))
    return estimator, messages


def choose_c(x, y, groups, config, seed):
    from sklearn.metrics import balanced_accuracy_score
    folds = grouped_folds(y, groups, config['inner_folds'], seed)
    attempts = []
    for c in config['c_grid']:
        predictions = np.empty(len(y), int); fold_details = []; failure = None
        try:
            for train, valid in folds:
                fit, messages = fit_linear(x[train], y[train], c, config)
                predictions[valid] = fit.predict(x[valid])
                fold_details.append(dict(training_indices=train.tolist(), validation_indices=valid.tolist(), warnings=messages))
        except Exception as exc:
            failure = f'{type(exc).__name__}: {exc}'
        attempts.append(dict(C=c, balanced_accuracy=float(balanced_accuracy_score(y, predictions)) if failure is None else None,
                             failure=failure, folds=fold_details))
    successful = [r for r in attempts if r['failure'] is None]
    if not successful:
        raise RuntimeError('Every predeclared regularization value failed')
    best = max(successful, key=lambda r: (r['balanced_accuracy'], -r['C']))
    return best['C'], attempts


def portable(estimator, feature_rule, common):
    scale, model = estimator.steps[0][1], estimator.steps[1][1]
    return FrozenPredictor(dict(common, kind='linear_probe', feature_rule=feature_rule),
        dict(coef=model.coef_[0], intercept=model.intercept_, mean=scale.mean_, scale=scale.scale_))


def nested_linear(slides, truth, groups, feature_rule, config, common):
    x = np.array([slide_vector(s.feats, feature_rule, config['top_k']) for s in slides]); y = np.asarray(truth, int)
    folds = grouped_folds(y, np.asarray(groups), config['outer_folds'], config['seed'])
    oof = [None]*len(slides); audits = []
    for number, (train, valid) in enumerate(folds):
        c, attempts = choose_c(x[train], y[train], np.asarray(groups)[train], config, config['seed']+number+1)
        fit, messages = fit_linear(x[train], y[train], c, config)
        predictor = portable(fit, feature_rule, common)
        for i in valid:
            oof[i] = dict(image_id=slides[i].metadata['slide_id'], truth=common['classes'][y[i]],
                          outer_fold=number, **predictor(slides[i].feats))
        audits.append(dict(outer_fold=number, training_ids=[slides[i].metadata['slide_id'] for i in train],
            validation_ids=[slides[i].metadata['slide_id'] for i in valid], selected_C=c, inner=attempts, warnings=messages))
    c, attempts = choose_c(x, y, np.asarray(groups), config, config['seed']+100)
    fit, messages = fit_linear(x, y, c, config)
    return oof, portable(fit, feature_rule, common), dict(outer=audits, all_training_C=c, all_training_inner=attempts, final_fit_warnings=messages)
