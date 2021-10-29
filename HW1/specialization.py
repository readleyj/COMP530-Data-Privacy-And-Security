from util import calculate_LM_cost_of_split


class SpecializationNode():
    DGHs = None
    RAW_DATASET = None

    def __init__(self, dgh_node_attribute_infos, parent=None):
        self.dgh_node_attribute_infos = dgh_node_attribute_infos
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

        self.attribute_name_to_idx_map = {
            attribute_info[0]: idx for idx, attribute_info in enumerate(self.dgh_node_attribute_infos)}

    def __eq__(self, other):
        for (_, value1), (_, value2) in zip(self.dgh_node_attribute_infos, other.dgh_node_attribute_infos):
            if value1 != value2:
                return False

        return True

    def calculate_records(self, data):
        raw_records, specialized_records = [], []

        for record_idx, record in data:
            num_matches = 0

            for attribute_name, value in self.dgh_node_attribute_infos:
                node_value_1, node_value_2 = value, record[attribute_name]

                dgh_info = self.DGHs[attribute_name]
                num_matches += int(dgh_info.has_ancestor_with_value(
                    node_value_1, node_value_2))

            if num_matches == len(self.dgh_node_attribute_infos):
                new_record = dict(record)

                for attribute_name, value in self.dgh_node_attribute_infos:
                    new_record[attribute_name] = value

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


def specialize(specialization_leaf_nodes, DGHs, k):
    new_specialization_tree_leaf_nodes = []

    for specialization_node in specialization_leaf_nodes:
        valid_splits = []
        split_cost_diffs = []

        for attribute_name, value in specialization_node.dgh_node_attribute_infos:
            new_specialization_nodes = []
            new_dgh_node_attribute_infos = specialization_node.dgh_node_attribute_infos[
                :]

            dgh_info = DGHs[attribute_name]
            dgh_node = dgh_info.value_to_node[value]
            attribute_idx = specialization_node.attribute_name_to_idx_map[attribute_name]

            for child_dgh_node in dgh_node.children:
                new_dgh_node_attribute_infos[attribute_idx] = (
                    attribute_name, child_dgh_node.value)
                new_specialization_node = SpecializationNode(
                    new_dgh_node_attribute_infos[:], parent=specialization_node)
                new_specialization_nodes.append(new_specialization_node)

            if all([node.num_records >= k for node in new_specialization_nodes]):
                valid_splits.append(new_specialization_nodes)
                split_cost_diffs.append(
                    specialization_node.LM_cost - calculate_LM_cost_of_split(new_specialization_nodes))

        if not valid_splits:
            new_specialization_tree_leaf_nodes.append(specialization_node)
            continue

        best_split_index = max(range(len(split_cost_diffs)),
                               key=lambda idx: split_cost_diffs[idx])
        best_split = valid_splits[best_split_index]

        for best_split_leaf in best_split:
            new_specialization_tree_leaf_nodes.append(best_split_leaf)

    else:
        for node1, node2 in zip(specialization_leaf_nodes, new_specialization_tree_leaf_nodes):
            if node1 == node2:
                continue
            else:
                break
        else:
            return specialization_leaf_nodes

        return specialize(new_specialization_tree_leaf_nodes, DGHs, k)
