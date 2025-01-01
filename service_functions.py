from time import time
# from math import exp, log
from typing import List, Union, Tuple, Optional, Dict, Set
from datetime import timedelta
import statistical_functions as stat_f


def get_alphabet(character_set: Set[str]) -> Tuple[str]:
    alphabets = ({'0', '1'}, {'A', 'C', 'G', 'T'},
                 {'A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H', 'I', 'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y', 'V'})
    for alphabet in alphabets:
        if not character_set - alphabet:
            return tuple(alphabet)


def get_alphabet_from_dict(pattern_msa_dict: Dict[str, str]) -> Tuple[str]:
    character_list = []
    for sequence in pattern_msa_dict.values():
        character_list += [i for i in sequence]

    return get_alphabet(set(character_list))


def compute_likelihood_of_tree(newick_text: str, pattern_msa: Optional[str] = None) -> Dict[str, Union[str, float,
                                                                                            int]]:
    start_time = time()
    log_likelihood_list, log_likelihood, likelihood = stat_f.compute_likelihood_of_tree(newick_text, pattern_msa)

    result = {'execution_time': convert_seconds(time() - start_time)}
    result.update({'likelihood_of_the_tree': likelihood})
    result.update({'log_likelihood_of_the_tree': log_likelihood})
    result.update({'log_likelihood_list': log_likelihood_list})

    return result


def convert_seconds(seconds: float) -> str:
    return str(timedelta(seconds=seconds))
