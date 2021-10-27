class DGHNode:
    def __init__(self, value, level, parent):
        self.value = value
        self.level = level
        self.parent = parent
        self.children = []
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
        self.value_to_desc_leaf_counts = {}
        self.value_to_node = {}

        self._calc_desc_leaf_counts(root_node)
        self._traverse(root_node)

    @property
    def total_num_leaves(self):
        return self.value_to_desc_leaf_counts[self.root_node.value]

    def level_dist_between_values(self, value1, value2):
        return abs(self.value_to_level_map[value1] - self.value_to_level_map[value2])

    def get_value_level(self, value):
        return self.value_to_level_map[value]

    def get_value_desc_leaf_count(self, value):
        return self.value_to_desc_leaf_counts[value]

    def lowest_common_ancestor(self, node_values):
        nodes = [self.value_to_node[value] for value in node_values]
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

        return new_node_values[0]

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
        self.value_to_desc_leaf_counts[value] = node.desc_leaf_count
        self.value_to_node[value] = node

        for child in node.children:
            self._traverse(child)
