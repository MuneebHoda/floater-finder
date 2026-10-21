"""Frozen-vector slide predictors; training dependencies are optional."""
from .pooling import slide_vector
from .linear_probe import FrozenPredictor, load_predictor

__all__ = ['slide_vector', 'FrozenPredictor', 'load_predictor']
