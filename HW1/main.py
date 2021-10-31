import csv
import glob
import os
import sys
import random
import heapq
import time

from dgh import DGHNode, DGHInfo
from util import calculate_equivalence_class
from specialization import SpecializationNode, specialize

if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    sys.stdout.write("Requires Python 3.x.\n")
    sys.exit(1)


def read_dataset(dataset_file: str):
    """ Read a dataset into a list and return.

    Args:
        dataset_file (str): path to the dataset file.

    Returns:
        list[dict]: a list of dataset rows.
    """
    result = []
    with open(dataset_file) as f:
        records = csv.DictReader(f)
        for row in records:
            result.append(row)
    return result


def write_dataset(dataset, dataset_file: str) -> bool:
    """ Writes a dataset to a csv file.

    Args:
        dataset: the data in list[dict] format
        dataset_file: str, the path to the csv file

    Returns:
        bool: True if succeeds.
    """
    assert len(dataset) > 0, "The anonymized dataset is empty."
    keys = dataset[0].keys()
    with open(dataset_file, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(dataset)
    return True


def read_DGH(DGH_file: str, attribute_name):
    """ Reads one DGH file and returns in desired format.

    Args:
        DGH_file (str): the path to DGH file.
    """

    last_node_by_level = []

    with open(DGH_file) as file:
        for line in file:
            level = line.rstrip().count('\t')
            attribute = line.strip()

            if level == 0:
                cur_node = DGHNode(attribute_name=attribute_name, value=attribute,
                                   parent=None, level=level)
            else:
                parent_node = last_node_by_level[level - 1]
                cur_node = DGHNode(attribute_name=attribute_name,
                                   value=attribute, parent=parent_node, level=level)
                parent_node.children.append(cur_node)

            if level >= len(last_node_by_level):
                last_node_by_level.append(cur_node)

            last_node_by_level[level] = cur_node

    root_node = last_node_by_level[0]

    return DGHInfo(root_node)


def read_DGHs(DGH_folder: str) -> dict:
    """ Read all DGH files from a directory and put them into a dictionary.

    Args:
        DGH_folder (str): the path to the directory containing DGH files.

    Returns:
        dict: a dictionary where each key is attribute name and values
            are DGHs in your desired format.
    """
    DGHs = {}

    for DGH_file in glob.glob(DGH_folder + "/*.txt"):
        attribute_name = os.path.basename(DGH_file)[:-4]
        DGHs[attribute_name] = read_DGH(DGH_file, attribute_name)

    return DGHs


def cost_MD(raw_dataset_file: str, anonymized_dataset_file: str,
            DGH_folder: str) -> float:
    """Calculate Distortion Metric (MD) cost between two datasets.

    Args:
        raw_dataset_file (str): the path to the raw dataset file.
        anonymized_dataset_file (str): the path to the anonymized dataset file.
        DGH_folder (str): the path to the DGH directory.

    Returns:
        float: the calculated cost.
    """
    raw_dataset = read_dataset(raw_dataset_file)
    anonymized_dataset = read_dataset(anonymized_dataset_file)
    assert(len(raw_dataset) > 0 and len(raw_dataset) == len(anonymized_dataset)
           and len(raw_dataset[0]) == len(anonymized_dataset[0]))
    DGHs = read_DGHs(DGH_folder)

    total_MD_cost = 0

    for attribute, dgh_info in DGHs.items():
        for idx in range(len(raw_dataset)):
            raw_record, anonymized_record = raw_dataset[idx], anonymized_dataset[idx]

            total_MD_cost += dgh_info.level_dist_between_values(
                raw_record[attribute], anonymized_record[attribute])

    return total_MD_cost


def cost_LM(raw_dataset_file: str, anonymized_dataset_file: str,
            DGH_folder: str) -> float:
    """Calculate Loss Metric (LM) cost between two datasets.

    Args:
        raw_dataset_file (str): the path to the raw dataset file.
        anonymized_dataset_file (str): the path to the anonymized dataset file.
        DGH_folder (str): the path to the DGH directory.

    Returns:
        float: the calculated cost.
    """
    raw_dataset = read_dataset(raw_dataset_file)
    anonymized_dataset = read_dataset(anonymized_dataset_file)
    assert(len(raw_dataset) > 0 and len(raw_dataset) == len(anonymized_dataset)
           and len(raw_dataset[0]) == len(anonymized_dataset[0]))
    DGHs = read_DGHs(DGH_folder)

    num_attrubutes = len(DGHs)
    attribute_weight = 1 / num_attrubutes

    total_LM_cost = 0

    for attribute, dgh_info in DGHs.items():
        dgh_total_leaves = dgh_info.total_num_leaves

        record_lm_cost = 0

        for record in anonymized_dataset:
            attribute_val = record[attribute]
            node_num_desc_leaf = dgh_info.get_desc_leaf_count_by_value(
                attribute_val)
            lm_val = (node_num_desc_leaf - 1) / (dgh_total_leaves)

            record_lm_cost += attribute_weight * lm_val

        total_LM_cost += record_lm_cost

    return total_LM_cost


def random_anonymizer(raw_dataset_file: str, DGH_folder: str, k: int,
                      output_file: str):
    """ K-anonymization a dataset, given a set of DGHs and a k-anonymity param.

    Args:
        raw_dataset_file (str): the path to the raw dataset file.
        DGH_folder (str): the path to the DGH directory.
        k (int): k-anonymity parameter.
        output_file (str): the path to the output dataset file.
    """
    raw_dataset = read_dataset(raw_dataset_file)
    DGHs = read_DGHs(DGH_folder)

    anonymized_dataset = [None] * len(raw_dataset)

    dataset_indices = list(range(len(raw_dataset)))
    random.shuffle(dataset_indices)

    num_pure_clusters = (len(dataset_indices) // k) - 1
    cluster_ranges = [[cluster_num * k, (cluster_num + 1) * k - 1]
                      for cluster_num in range(num_pure_clusters)] + [[num_pure_clusters * k, len(dataset_indices) - 1]]
    index_ranges = [[dataset_indices[idx] for idx in
                     range(cluster_range[0], cluster_range[1] + 1)] for cluster_range in cluster_ranges]
    clusters = [[raw_dataset[idx] for idx in index_range]
                for index_range in index_ranges]

    for cluster_idx in range(len(clusters)):
        cluster = clusters[cluster_idx]
        index_range = index_ranges[cluster_idx]

        calculate_equivalence_class(DGHs, cluster)

        for idx in range(len(index_range)):
            record_idx = index_range[idx]
            record = cluster[idx]

            anonymized_dataset[record_idx] = record

    write_dataset(anonymized_dataset, output_file)


def clustering_anonymizer(raw_dataset_file: str, DGH_folder: str, k: int,
                          output_file: str):
    """ Clustering-based anonymization a dataset, given a set of DGHs.

    Args:
        raw_dataset_file (str): the path to the raw dataset file.
        DGH_folder (str): the path to the DGH directory.
        k (int): k-anonymity parameter.
        output_file (str): the path to the output dataset file.
    """
    raw_dataset = read_dataset(raw_dataset_file)
    DGHs = read_DGHs(DGH_folder)

    def calc_dist_between_records(record1, record2):
        raw_records = [record1, record2]
        anonymized_records = [dict(record1), dict(record2)]

        total_MD_cost = 0

        calculate_equivalence_class(DGHs, anonymized_records)

        for attribute, dgh_info in DGHs.items():
            for idx in range(len(raw_records)):
                raw_record, anonymized_record = raw_records[idx], anonymized_records[idx]

                total_MD_cost += dgh_info.level_dist_between_values(
                    raw_record[attribute], anonymized_record[attribute])

        return total_MD_cost

    anonymized_dataset = [None] * len(raw_dataset)
    clustering_heap = []

    unmarked_record_indices = set(range(len(raw_dataset)))
    first_unmarked_index = 0

    while len(unmarked_record_indices) >= k:
        cluster_size = k

        if len(unmarked_record_indices) // k == 1 and len(unmarked_record_indices) % k > 0:
            cluster_size = len(unmarked_record_indices)

        rec = raw_dataset[first_unmarked_index]

        for record_idx in unmarked_record_indices:
            if record_idx == first_unmarked_index:
                continue

            record = raw_dataset[record_idx]

            heapq.heappush(clustering_heap, [
                calc_dist_between_records(rec, record), record_idx, record])

        closest_entries = heapq.nsmallest(cluster_size - 1, clustering_heap)
        entry_cluster = closest_entries + [[-1, first_unmarked_index, rec]]

        record_cluster = [entry[2] for entry in entry_cluster]
        record_indices = [entry[1] for entry in entry_cluster]

        calculate_equivalence_class(DGHs, record_cluster)

        for record_idx, record in zip(record_indices, record_cluster):
            anonymized_dataset[record_idx] = record
            unmarked_record_indices.remove(record_idx)

        if unmarked_record_indices:
            first_unmarked_index = min(unmarked_record_indices)

        clustering_heap.clear()

    write_dataset(anonymized_dataset, output_file)


def topdown_anonymizer(raw_dataset_file: str, DGH_folder: str, k: int,
                       output_file: str):
    """ Top-down anonymization a dataset, given a set of DGHs.

    Args:
        raw_dataset_file (str): the path to the raw dataset file.
        DGH_folder (str): the path to the DGH directory.
        k (int): k-anonymity parameter.
        output_file (str): the path to the output dataset file.
    """
    raw_dataset = read_dataset(raw_dataset_file)
    anonymized_dataset = [None] * len(raw_dataset)
    DGHs = read_DGHs(DGH_folder)

    SpecializationNode.DGHs = DGHs
    SpecializationNode.RAW_DATASET = raw_dataset

    dgh_root_node_attributes_info = [
        (DGH.root_node.attribute_name, DGH.root_node.value) for DGH in DGHs.values()]

    specialization_tree_root_node = SpecializationNode(
        dgh_root_node_attributes_info)
    specialization_tree_leaf_nodes = None

    specialization_tree_leaf_nodes = specialize(
        [specialization_tree_root_node], DGHs, k)

    for specialization_node in specialization_tree_leaf_nodes:
        for record_idx, record in specialization_node.anonymized_records:
            anonymized_dataset[record_idx] = record

    write_dataset(anonymized_dataset, output_file)


if len(sys.argv) < 6:
    print(
        f"Usage: python3 {sys.argv[0]} algorithm DGH-folder raw-dataset.csv anonymized.csv k")
    print(f"\tWhere algorithm is one of [clustering, random, topdown]")
    sys.exit(1)

algorithm = sys.argv[1]
if algorithm not in ['clustering', 'random', 'topdown']:
    print("Invalid algorithm.")
    sys.exit(2)

dgh_path = sys.argv[2]
raw_file = sys.argv[3]
anonymized_file = sys.argv[4]
k = int(sys.argv[5])

function = eval(f"{algorithm}_anonymizer")

start_time = time.time()

function(raw_file, dgh_path, k, anonymized_file)

end_time = time.time()
elapsed_time = end_time - start_time

cost_md = cost_MD(raw_file, anonymized_file, dgh_path)
cost_lm = cost_LM(raw_file, anonymized_file, dgh_path)
print(
    f"Results of {k}-anonimity:\n\tCost_MD: {cost_md}\n\tCost_LM: {cost_lm:.2f}\n\tElapsed Time: {elapsed_time:.2f}s\n")

# Sample usage:
# python3 main.py clustering DGHs/ adult-hw1.csv result.csv 300
