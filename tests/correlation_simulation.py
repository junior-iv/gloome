from gloome.tree.tree import Tree
from typing import Union, Any
from pathlib import Path
from json import dumps


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
    categories_quantity = 64
    alpha = 0.5
    pi_1 = 0.5
    branch_lengths = 0.5
    seed = 24

    Tree.generate_scatter_plot(taxa_list, sites_quantity, categories_quantity, alpha, pi_1, branch_lengths, seed)


main()
