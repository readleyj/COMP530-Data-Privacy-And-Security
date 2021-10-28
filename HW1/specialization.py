from os import stat


# Need to represent a specialization tree node somehow
# Need to represent the tree itself
# In each 'iteration', go through leaves of the specialization tree, go through each node of each leaf, and split
# The number of nodes of each node should be maintained. Will be used to check whether k-anonymity is satisified
# Need a way to apply a certain specialization to the dataset. Maybe a apply_specialization() method on the node class
# 2 classes: SpecializationNode and SpecializationTree
# SpecializationNode maintains the root node and leaf nodes
# SpecializationNode has n-number of DGHNodes
# Maybe should have DGHInfo instead
# Need to efficiently count number of records satisfying specialization

class SpecializationNode():
    DGHs = None
    RAW_DATASET = None

    def __init__(self, dgh_nodes, parent=None):
        self.dgh_nodes = dgh_nodes
        self.parent = parent
        self.children = []
        self.raw_records = None
        self.anonymized_records = None

        if not parent:
            self.raw_records, self.anonymized_records = self.calculate_records(
                enumerate(self.RAW_DATASET))
        else:
            self.raw_records, self.anonymized_records = self.calculate_records(
                self.parent.raw_records)

        self.num_records = len(self.raw_records)
        self.LM_cost = self.calc_LM_cost()
        self.dgh_attribute_name_to_index_map = {
            node.attribute_name: idx for idx, node in enumerate(self.dgh_nodes)}

    def __eq__(self, other):
        for dgh_node1, dgh_node2 in zip(self.dgh_nodes, other.dgh_nodes):
            if dgh_node1.value != dgh_node2.value:
                return False

        return True

    def calculate_records(self, data):
        raw_records, specialized_records = [], []

        for record_idx, record in data:
            num_matches = 0

            for dgh_node in self.dgh_nodes:
                attribute_name = dgh_node.attribute_name

                node_value_1, node_value_2 = dgh_node.value, record[attribute_name]

                dgh_info = self.DGHs[attribute_name]
                num_matches += int(dgh_info.has_ancestor_with_value(
                    node_value_1, node_value_2)) or node_value_1 == node_value_2

            if num_matches == len(self.dgh_nodes):
                new_record = dict(record)

                for dgh_node in self.dgh_nodes:
                    new_record[dgh_node.attribute_name] = dgh_node.value

                raw_records.append((record_idx, record))
                specialized_records.append((record_idx, new_record))

        return raw_records, specialized_records

    def calc_LM_cost(self):
        num_attrubutes = len(self.DGHs)
        attribute_weight = 1 / num_attrubutes

        total_LM_cost = 0

        for attribute, dgh_info in self.DGHs.items():
            dgh_total_leaves = dgh_info.total_num_leaves

            record_lm_cost = 0

            for _, record in self.anonymized_records:
                attribute_val = record[attribute]
                node_num_desc_leaf = dgh_info.value_to_desc_leaf_counts[attribute_val]
                lm_val = (node_num_desc_leaf - 1) / (dgh_total_leaves)

                record_lm_cost += attribute_weight * lm_val

            total_LM_cost += record_lm_cost

        return total_LM_cost
