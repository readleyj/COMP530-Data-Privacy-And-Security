def calculate_equivalence_class(DGHs, record_cluster):
    for attribute, dgh_info in DGHs.items():
        attribute_values = [record[attribute]
                            for record in record_cluster]
        lca_value = dgh_info.lowest_common_ancestor(attribute_values)

        for record in record_cluster:
            record[attribute] = lca_value