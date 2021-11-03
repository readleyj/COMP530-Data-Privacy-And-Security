class DGHNode:
    def __init__(self, attribute_name, value, level, parent):
        self.attribute_name = attribute_name
        self.value = value
        self.level = level
        self.parent = parent
        self.children = []
        self.ancestors = set()
        self.desc_leaf_count = None

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def is_root(self):
        return self.parent is None


class DGHInfo:
    def __init__(self, root_node):
        self.root_node = root_node

        self.value_to_level_map = {}
        self.value_to_desc_leaf_counts_map = {}
        self.value_to_node_map = {}
        self.lca_cache = {}

        self._calc_desc_leaf_counts(root_node)
        self._traverse(root_node)

    @property
    def total_num_leaves(self):
        return self.value_to_desc_leaf_counts_map[self.root_node.value]

    def get_desc_leaf_count_by_value(self, value):
        return self.value_to_desc_leaf_counts_map[value]

    def get_node_by_value(self, value):
        return self.value_to_node_map[value]

    def level_dist_between_values(self, value1, value2):
        return abs(self.value_to_level_map[value1] - self.value_to_level_map[value2])

    def lowest_common_ancestor(self, node_values):
        if node_values not in self.lca_cache:
            nodes = [self.get_node_by_value(value) for value in node_values]
            highest_level = min([node.level for node in nodes])
            new_nodes = []

            for node in nodes:
                cur_node = node

                while cur_node.level > highest_level:
                    cur_node = cur_node.parent

                new_nodes.append(cur_node)

            new_node_values = [node.value for node in new_nodes]

            while len(new_node_values) != new_node_values.count(new_node_values[0]):
                for idx, new_node in enumerate(new_nodes):
                    new_nodes[idx] = new_node.parent
                    new_node_values[idx] = new_nodes[idx].value

            self.lca_cache[node_values] = new_node_values[0]

        return self.lca_cache[node_values]

    def has_ancestor_with_value(self, value_1, value_2):
        """
        Check if a node with value_1 is an ancestor of node with value_2
        """
        dgh_node_2 = self.get_node_by_value(value_2)
        return value_1 in dgh_node_2.ancestors

    def _calc_desc_leaf_counts(self, node):
        if node.is_leaf:
            desc_leaf_count = 1
        else:
            desc_leaf_count = sum([self._calc_desc_leaf_counts(child)
                                   for child in node.children])

        node.desc_leaf_count = desc_leaf_count
        return desc_leaf_count

    def _traverse(self, node):
        value = node.value

        self.value_to_level_map[value] = node.level
        self.value_to_desc_leaf_counts_map[value] = node.desc_leaf_count
        self.value_to_node_map[value] = node

        for child in node.children:
            child.ancestors = set.union(
                node.ancestors, set([value, child.value]))
            self._traverse(child)
