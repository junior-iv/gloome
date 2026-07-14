from gloome.tree.tree import Tree
from typing import Union, Any
from pathlib import Path
from json import dumps

BIN_DIR = Path.cwd().parent


def read_file(file_path: Path) -> str:
    if file_path.is_file():
        with open(file_path, 'r') as f:
            return f.read()
    return ''


def write_file(file_path: Path, data: Union[str, Any]):
    file_path = file_path.parent.joinpath(f'{file_path.stem}_new{file_path.suffix}')
    with open(file_path, 'w') as f:
        if isinstance(data, str):
            f.write(data)
        else:
            f.write(dumps(data))


def main():
    taxa_list = [8, 16, 32, 64, 128, 256]
    sites_quantity = 100
    categories_quantity = 4
    alpha = 0.5
    pi_1 = 0.5
    branch_lengths = 0.5
    seed = 24
    fasta_text = None
    newick_text = None
    # seed = 42
    #
    # Tree.generate_scatter_plot(taxa_list, sites_quantity, categories_quantity, alpha, pi_1, branch_lengths, seed)
    #
    dirname = BIN_DIR
    msa_file = dirname.joinpath('gloome/data/initial_data/msa/patternMSA0.msa')
    tree_file = dirname.joinpath('gloome/data/initial_data/tree/newickTree0.tree')
    # msa_file = dirname.joinpath('gloome/data/initial_data/msa/patternMSA11.fasta')
    # tree_file = dirname.joinpath('gloome/data/initial_data/tree/newickTree11.nwk')
    fasta_text = read_file(msa_file)
    newick_text = read_file(tree_file)
    file_path = dirname.joinpath('g')
    tree_data = {'pi_1': pi_1,
                 'alpha': alpha,
                 'categories_quantity': categories_quantity}
    gloome_tree = Tree(newick_text, msa=fasta_text, **tree_data)

    print(f'\trate_vector (4 Gamma categories): {[round(float(r), 4) for r in gloome_tree.rate_vector]}')

    gloome_tree.calculate_tree()
    gloome_tree.set_posterior_rates_vector()
    gloome_tree.posterior_rates_to_tsv(f'{file_path}/PosteriorRates.tsv')
    gloome_tree.tree_to_tsv(f'{file_path}/Branches.tsv', mode='branch_tsv', taking_into_coefficient=True)
    gloome_tree.set_pearson_correlation_vector(0.7, 2)
    gloome_tree.pearson_correlation_to_tsv(f'{file_path}/PearsonCorrelation.tsv')
    # len_seq = len(next(iter(gloome_tree.msa.values())))
    #
    # nodes_list = gloome_tree.get_list_nodes_info(filters={'node_type': ['node', 'leaf']}, only_node_list=True)
    # # gloome_tree.get_leaves()
    #
    # # site_probabilities = []
    # # site_probabilities_dict = dict
    # # for i in range(len(next(iter(gloome_tree.msa.values())))):
    # #     probabilities = []
    # #     for node in nodes_list:
    # #         probabilities.append(node.probability_vector_loss[i])
    # #         probabilities.append(node.probability_vector_gain[i])
    # #
    # #     print(sum(np.array(probabilities) > 0.5))
    # #     if sum(np.array(probabilities) > 0.7) > 4:
    # #         site_probabilities_dict.update({i: probabilities})
    # #     site_probabilities.append(probabilities)
    # # print(site_probabilities_dict)
    #
    # nodes_list = gloome_tree.get_list_nodes_info(filters={'node_type': ['node', 'leaf']}, only_node_list=True)
    # site_probabilities = []
    # indices = []
    # for i in range(len(next(iter(gloome_tree.msa.values())))):
    #     probabilities = []
    #     for node in nodes_list:
    #         probabilities.append(node.probability_vector_loss[i])
    #         probabilities.append(node.probability_vector_gain[i])
    #
    #     if sum(np.array(probabilities) > 0.7) > 1:
    #         print(i, sum(np.array(probabilities) > 0.7))
    #         indices.append(i)
    #     site_probabilities.append(probabilities)
    # print(*tuple(indices), sep='\n')
    # print(*tuple(site_probabilities), sep='\n')
    # print(*tuple(np.array(site_probabilities)[indices]), sep='\n')
    # probabilities = np.array(site_probabilities)[indices]
    # print()
    # unique_item = np.unique(indices)
    # idx1, idx2 = np.triu_indices(len(unique_item), k=1)
    # couples = np.column_stack((unique_item[idx1], unique_item[idx2]))
    # # couples = list(combinations(set(indices), 2))
    # print(*tuple(np.array(site_probabilities)[couples]), sep='\n\n')
    #
    # for i, j in couples:
    #     r_corr, p_val = pearsonr(site_probabilities[i], site_probabilities[j])
    #     print(f" I = {i}  J {j}  Pearson r = {r_corr:.4f}  (p = {p_val:.3e})")
    #
    # for probabilities_1, probabilities_2 in np.array(site_probabilities)[couples]:
    #     r_corr, p_val = pearsonr(probabilities_1, probabilities_2)
    #     print(f"Pearson r = {r_corr:.4f}  (p = {p_val:.3e})")
    # # return r_corr, true_rates, gloome_tree.posterior_rates
    #
    # # for node in gloome_tree.get_leaves():
    # #     print()
    # #     print(node.name)
    # #     print(node.probability_vector_loss)
    # #     print()
    # #     print(node.probability_vector_gain)
    # #     print()
    # #     print(node.branch_probability_vector)
    # #     print()
    # #     break
    # #
    # # nodes_list = gloome_tree.get_list_nodes_info(only_node_list=True)
    # # for i in range(len(next(iter(gloome_tree.msa.values())))):
    # #     probabilities = []
    # #     for node in nodes_list:
    # #         probabilities.append(node.probability_vector_loss)
    # #         probabilities.append(node.probability_vector_gain)




main()
