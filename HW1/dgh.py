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

        self._calc_desc_leaf_counts(root_node)
        self._traverse(root_node)

    @property
    def total_num_leaves(self):
        return self.get_value_desc_leaf_count[self.root_node.value]

    def get_value_level(self, value):
        return self.value_to_level_map[value]

    def get_value_desc_leaf_count(self, value):
        return self.value_to_desc_leaf_counts[value]

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

        for child in node.children:
            self._traverse(child)
