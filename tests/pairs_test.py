"""Unit tests for gloome.tree.pairs, the memory-bounded pair-correlation / null engine.

Run: python -m pytest tests/test_pairs.py -q
"""
import numpy as np
import pytest

from gloome.tree import pairs
from gloome.tree.tree import Tree


def _matrix(n_rows=60, n_cols=25, seed=0):
    rng = np.random.default_rng(seed)
    m = rng.random((n_rows, n_cols))
    m[5] = m[3]          # identical rows -> r == 1 ties
    m[7] = 1 - m[3]      # r == -1
    return m


@pytest.mark.parametrize('block_elements', [7, 64, 1 << 22])
def test_upper_pairs_match_corrcoef_in_triu_order(block_elements):
    m = _matrix()
    centered, norms = pairs.centered_rows(m)
    chunks = list(pairs.iter_upper_pairs(centered, norms, block_elements=block_elements))
    i = np.concatenate([c[0] for c in chunks])
    j = np.concatenate([c[1] for c in chunks])
    r = np.concatenate([c[2] for c in chunks])
    ti, tj = np.triu_indices(len(m), k=1)
    assert np.array_equal(i, ti) and np.array_equal(j, tj)
    assert np.allclose(r, np.corrcoef(m)[ti, tj], atol=1e-12)


@pytest.mark.parametrize('block_elements', [5, 100, 1 << 22])
def test_bin_blocks_cover_every_pair_once_per_code(block_elements):
    m = _matrix()
    k = 4
    categories = np.random.default_rng(1).integers(0, k, len(m))
    categories[:3] = 2   # make sure some category has several rows
    centered, norms = pairs.centered_rows(m)
    got = {}
    for code, r in pairs.iter_bin_blocks(centered, norms, categories, k, block_elements=block_elements):
        got.setdefault(code, []).append(r)
    ti, tj = np.triu_indices(len(m), k=1)
    expected_codes = pairs.pair_codes(categories[ti], categories[tj], k)
    full = np.corrcoef(m)[ti, tj]
    assert set(got) == set(np.unique(expected_codes).tolist())
    for code, chunks in got.items():
        assert np.allclose(np.sort(np.concatenate(chunks)), np.sort(full[expected_codes == code]), atol=1e-12)


def test_weighted_benjamini_hochberg_equals_expanded():
    rng = np.random.default_rng(2)
    p = np.round(rng.random(40), 2)            # many ties
    w = rng.integers(1, 6, 40)
    expanded = np.repeat(p, w)
    q_expanded = Tree.benjamini_hochberg(expanded)
    q_weighted = pairs.benjamini_hochberg_weighted(p, w)
    assert np.allclose(np.repeat(q_weighted, w), q_expanded)


def test_histogram_p_values_are_conservative_and_close():
    rng = np.random.default_rng(3)
    null_values = np.tanh(rng.normal(0, 0.4, 200_000))
    exact = pairs.NullDistribution(1, exact_limit=10 ** 9)
    hist = pairs.NullDistribution(1, exact_limit=0)
    for chunk in np.array_split(null_values, 7):
        exact.add(0, chunk)
        hist.add(0, chunk)
    observed = np.tanh(rng.normal(0, 0.6, 5_000))
    p_exact = pairs.empirical_p_exact(np.abs(observed), exact.samples()[0])
    p_hist = hist.empirical_p_table()[0, pairs.abs_index(observed, hist.hist_bins)]
    assert np.all(p_hist >= p_exact - 1e-15)
    assert np.max(p_hist - p_exact) < 1e-3


def test_exact_null_switches_to_histogram_at_limit():
    null = pairs.NullDistribution(2, exact_limit=100)
    null.add(0, np.linspace(-0.5, 0.5, 60))
    assert null.exact
    null.add(3, np.linspace(-0.5, 0.5, 60))
    assert not null.exact and null.counts.sum() == 120 and null.size == 120


def test_ties_count_as_at_least_as_extreme():
    # r == 1 observed against a null spike at 1 - 2e-16 (same value up to rounding).
    null_values = np.array([1 - 2e-16] * 50 + [0.1] * 50)
    p = pairs.empirical_p_exact(np.array([1.0]), null_values)
    assert p[0] == pytest.approx(51 / 101)
    hist = pairs.NullDistribution(1, exact_limit=0)
    hist.add(0, null_values)
    assert hist.empirical_p_table()[0, pairs.abs_index(np.array([1.0]), hist.hist_bins)][0] == pytest.approx(51 / 101)


def test_histogram_beta_fit_recovers_parameters():
    rng = np.random.default_rng(4)
    a, b = 8.0, 8.0
    sample = 2 * rng.beta(a, b, 400_000) - 1
    null = pairs.NullDistribution(1, exact_limit=0)
    null.add(0, sample)
    params = null.fit_beta(0)
    assert params is not None
    assert params[0] == pytest.approx(a, rel=0.03) and params[1] == pytest.approx(b, rel=0.03)
