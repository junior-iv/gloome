from typing import Optional, Dict, Union, List
from collections import deque


class Node:
    father: Optional['Node']
    children: list
    name: str
    distance_to_father: float

    def __init__(self, name: Optional[str]):
        self.father = None
        self.children = []
        self.name = name
        self.distance_to_father = 0

    def __str__(self) -> str:
        return self.get_name(self, True)

    def __dir__(self) -> list:
        return ['children', 'distance_to_father', 'father', 'name']

    def list_nodes_info(self, reverse: bool = False, with_additional_details: bool = False, mode: Optional[
                        str] = None, filters: Optional[Dict[str, List[Union[float, int, str, List[float]]]]] = None
                        ) -> List[Dict[str, Union[float, bool, str, List[float]]]]:
        """
        Retrieve a list of descendant nodes from a given node, including the node itself or retrieve a list of
        descendant nodes from the current instance of the `Tree` class.

        This function collects all child nodes of the specified `node`, including the `node` itself, or collects all
        child nodes of the current instance of the `Tree` class if `node` is not provided. The function
        returns these nodes names as a list.

        Args:
            reverse (bool, optional): If `True`, the resulting list of nodes will be in reverse order.
                                      If `False` (default), the nodes will be listed in their natural
                                      traversal order.
            with_additional_details (bool, optional): `False` (default).
            mode (Optional[str]): `None` (default), 'pre-order', 'in-order', 'post-order', 'level-order'.
            filters (Dict, optional):
        Returns:
            list: A list of nodes names including the specified `node` (or the current instance's nodes  names) and its
                                    children. The list is ordered according to the `reverse` argument.
        """
        list_result = []
        mode = 'pre-order' if mode is None or mode.lower() not in ('pre-order', 'in-order', 'post-order', 'level-order'
                                                                   ) else mode.lower()

        def get_list(trees_node: Node) -> None:
            nonlocal list_result, reverse, filters, mode, with_additional_details

            nodes_info = trees_node.get_nodes_info()
            if trees_node.check_filter_compliance(filters, nodes_info):
                if mode == 'pre-order':
                    list_result.append(nodes_info if with_additional_details else trees_node.name)

                for i, child in enumerate(trees_node.children[::-1]) if reverse else enumerate(trees_node.children):
                    get_list(child)
                    if mode == 'in-order' and i == 0:
                        list_result.append(nodes_info if with_additional_details else trees_node.name)

                if not trees_node.children:
                    if mode == 'in-order':
                        list_result.append(nodes_info if with_additional_details else trees_node.name)

                if mode == 'post-order':
                    list_result.append(nodes_info if with_additional_details else trees_node.name)
            else:
                for i, child in enumerate(trees_node.children[::-1]) if reverse else enumerate(trees_node.children):
                    get_list(child)

        if mode == 'level-order':
            queue = deque([self])
            while queue:
                newick_node = queue.popleft()
                if newick_node.check_filter_compliance(filters, newick_node.get_nodes_info()):
                    list_result.append(newick_node.get_nodes_info() if with_additional_details else newick_node.name)

                if newick_node.children[::-1] if reverse else newick_node.children:
                    for nodes_child in newick_node.children:
                        queue.append(nodes_child)
        else:
            get_list(self)

        return list_result

    def get_nodes_info(self) -> Dict[str, Union[float, bool, str, List[float]]]:
        lavel = 1
        full_distance = [self.distance_to_father]
        father = self.father
        if father:
            father_name = father.name
            node_type = 'node'
            while father:
                full_distance.append(father.distance_to_father)
                lavel += 1
                father = father.father
        else:
            father_name = ''
            node_type = 'root'

        if not self.children:
            node_type = 'leaf'

        info = {'node': self.name, 'distance': full_distance[0],
                'lavel': lavel, 'node_type': node_type, 'father_name': father_name,
                'full_distance': full_distance, 'children': [i.name for i in self.children]}

        return info

    @staticmethod
    def check_filter_compliance(filters: Optional[Dict[str, List[Union[float, int, str, List[float]]]]], info: Dict[str,
                                Union[float, bool, str, list[float]]]) -> bool:
        permission = 0
        if filters:
            for key in filters.keys():
                for value in filters.get(key):
                    permission += sum(k == key and info[k] == value for k in info)
        else:
            permission = 1

        return bool(permission)

    @classmethod
    def subtree_to_newick(cls, node: Optional['Node'], reverse: bool = False) -> str:
        """This method is for internal use only."""
        node_list = node.children[::-1] if reverse else node.children
        if node_list:
            result = '('
            for child in node_list:
                result += (f'{cls.subtree_to_newick(child, reverse) if child.children else child.name}:'
                           f'{child.distance_to_father},')
            result = result[:-1] + ')'
        else:
            result = f'{node.name}:{node.distance_to_father}'
        return result

    @classmethod
    def get_name(cls, node: Optional['Node'], is_full_name: bool = False) -> str:
        return (f'{cls.subtree_to_newick(node) if node.children and is_full_name else node.name}:'
                f'{node.distance_to_father:.5f}')

    def add_child(self, child: Optional['Node'], distance_to_father: float) -> None:
        self.children.append(child)
        child.father = self
        child.distance_to_father = distance_to_father

    def get_full_distance_to_leafs(self) -> float:
        list_result = []
        child = self
        while True:
            list_result.append({'node': child, 'distance': child.distance_to_father})
            if not child.children:
                break
            child = child.children[0]
        return sum([i['distance'] for i in list_result])

    def get_full_distance_to_father(self) -> float:
        list_result = []
        father = self
        while True:
            list_result.append({'node': father, 'distance': father.distance_to_father})
            if not father.father:
                break
            father = father.father
        return sum([i['distance'] for i in list_result])
