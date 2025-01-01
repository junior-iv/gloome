import numpy as np
# from tree import Tree, Node
from scipy.linalg import expm


def get_jukes_cantor_qmatrix(branch_length: float, alphabet_size: int) -> np.ndarray:
    qmatrix = np.ones((alphabet_size, alphabet_size))
    np.fill_diagonal(qmatrix, 1 - alphabet_size)
    qmatrix = qmatrix * 1 / (alphabet_size - 1)

    return expm(qmatrix * branch_length)
