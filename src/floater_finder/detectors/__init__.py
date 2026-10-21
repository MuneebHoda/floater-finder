"""Training-only morphology anomaly prototypes; never an automatic tissue action."""
from .contextual_similarity import anomaly_features, cohort_distance

__all__ = ['anomaly_features', 'cohort_distance']
