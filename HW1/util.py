def calculate_equivalence_class(DGHs, record_cluster):
    for attribute, dgh_info in DGHs.items():
        attribute_values = tuple(record[attribute] for record in record_cluster)
        lca_value = dgh_info.lowest_common_ancestor(attribute_values)

        for record in record_cluster:
            record[attribute] = lca_value


def calculate_LM_cost_of_split(specialization_split):
    return sum([node.LM_cost for node in specialization_split])


def calc_dist_between_records(record1, record2, DGHs):
    raw_records = [record1, record2]
    anonymized_records = [dict(record1), dict(record2)]

    total_MD_cost = 0

    calculate_equivalence_class(DGHs, anonymized_records)

    for attribute, dgh_info in DGHs.items():
        for idx in range(len(raw_records)):
            raw_record, anonymized_record = raw_records[idx], anonymized_records[idx]

            total_MD_cost += dgh_info.level_dist_between_values(
                raw_record[attribute], anonymized_record[attribute]
            )

    return total_MD_cost
