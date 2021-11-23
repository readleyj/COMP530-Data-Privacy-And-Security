from collections import Counter

import matplotlib.pyplot as plt
import numpy as np

LABELS = ["", "frontpage", "news", "tech", "local", "opinion", "on-air", "misc", "weather",
          "msn-news", "health", "living", "business", "msn-sports", "sports", "summary", "bbs", "travel"]


def read_dataset(filename):
    """
        Reads the dataset with given filename.

        Args:
            filename (str): Path to the dataset file
        Returns:
            Dataset rows as a list of lists.
    """

    result = []
    with open(filename, "r") as f:
        for _ in range(7):
            next(f)
        for line in f:
            sequence = line.strip().split(" ")
            result.append([int(i) for i in sequence])
    return result


def get_counts(dataset):
    counts = Counter(
        category_idx for row in dataset for category_idx in row)
    return [counts[category_idx] for category_idx in range(1, len(LABELS))]


def draw_histogram(counts):
    fig, ax = plt.subplots()
    category_indices = list(range(1, len(LABELS)))

    plt.hist(category_indices, weights=counts, bins=np.arange(
        min(category_indices), max(category_indices) + 2), align='left', edgecolor='black')
    plt.xticks(range(1, max(category_indices) + 1), LABELS[1:], rotation=90)

    ax.set_xlabel('# of visits in each category')
    ax.xaxis.set_label_position('top')
    ax.set_ylabel('Number of visits')

    return fig


def get_histogram(dataset: list):
    """
        Creates a histogram of given counts for each category and saves it to a file.

        Args:
            dataset (list of lists): The MSNBC dataset

        Returns:
            Ordered list of counts for each page category (frontpage, news, tech, ..., travel)
            Ex: [123, 383, 541, ..., 915]
    """

    counts = get_counts(dataset)

    histogram = draw_histogram(counts)
    histogram.savefig('np-histogram.png', dvi=1000, bbox_inches='tight')

    return counts


def add_laplace_noise(real_answer: list, sensitivity: float, epsilon: float):
    """
        Adds laplace noise to query's real answers.

        Args:
            real_answer (list): Real answers of a query -> Ex: [92.85, 57.63, 12, ..., 15.40]
            sensitivity (float): Sensitivity
            epsilon (float): Privacy parameter
        Returns:
            Noisy answers as a list.
            Ex: [103.6, 61.8, 17.0, ..., 19.62]
    """

    return [num + np.random.laplace(0, sensitivity / epsilon) for num in real_answer]


def truncate(dataset: list, n: int):
    """
        Truncates dataset according to truncation parameter n.

        Args:
            dataset: original dataset
            n (int): truncation parameter
        Returns:
            truncated_dataset: truncated version of original dataset
    """
    return [row[:n] for row in dataset]


def get_dp_histogram(dataset: list, n: int, epsilon: float):
    """
        Truncates dataset with parameter n and calculates differentially private histogram.

        Args:
            dataset (list of lists): The MSNBC dataset
            n (int): Truncation parameter
            epsilon (float): Privacy parameter
        Returns:
            Differentially private histogram as a list
    """

    sensitivity = n
    truncated_histogram = truncate(dataset, n)
    real_answers = get_counts(truncated_histogram)

    return add_laplace_noise(real_answers, sensitivity, epsilon)


def calculate_average_error(actual_hist, noisy_hist):
    """
        Calculates error according to the equation stated in part (e).

        Args: Actual histogram (list), Noisy histogram (list)
        Returns: Error (Err) in the noisy histogram (float)
    """

    num_bins = len(actual_hist)

    return sum([abs(actual_val - noise_val)
                for actual_val, noise_val in zip(actual_hist, noisy_hist)]) / num_bins


def n_experiment(dataset, n_values: list, epsilon: float):
    """
        Function for the experiment explained in part (f).
        n_values is a list, such as: [1, 6, 11, 16 ...]
        Returns the errors as a list: [1256.6, 1653.5, ...] such that 1256.5 is the error when n=1,
        1653.5 is the error when n = 6, and so forth.
    """
    errors = []
    actual_hist = get_counts(dataset)

    for n in n_values:
        run_errors = []

        for _ in range(30):
            noisy_hist = get_dp_histogram(dataset, n, epsilon)
            error = calculate_average_error(actual_hist, noisy_hist)

            run_errors.append(error)

        errors.append(np.average(run_errors))

    return errors


def epsilon_experiment(dataset, n: int, eps_values: list):
    """
        Function for the experiment explained in part (g).
        eps_values is a list, such as: [0.0001, 0.001, 0.005, 0.01, 0.05, 0.1, 1.0]
        Returns the errors as a list: [9786.5, 1234.5, ...] such that 9786.5 is the error when eps = 0.0001,
        1234.5 is the error when eps = 0.001, and so forth.
    """
    errors = []
    actual_hist = get_counts(dataset)

    for epsilon in eps_values:
        run_errors = []

        for _ in range(30):
            noisy_hist = get_dp_histogram(dataset, n, epsilon)
            error = calculate_average_error(actual_hist, noisy_hist)

            run_errors.append(error)

        errors.append(np.average(run_errors))

    return errors


def extract(dataset):
    """
        Extracts the first 1000 sequences and truncates them to n=1
    """
    return truncate(dataset[:1000], 1)


def most_visited_exponential(smaller_dataset, epsilon):
    """
        Using the Exponential mechanism, calculates private response for query:
        "Which category (1-17) received the highest number of page visits?"

        Returns 1 for frontpage, 2 for news, 3 for tech, etc.
    """
    SENSITIVITY = 1

    scores = get_counts(smaller_dataset)
    probabilities = [np.exp(epsilon * score / (2 * SENSITIVITY))
                     for score in scores]
    probabilities = probabilities / np.linalg.norm(probabilities, ord=1)

    return np.random.choice(range(1, len(scores) + 1), 1, p=probabilities)[0]


def exponential_experiment(dataset, eps_values: list):
    """
        Function for the experiment explained in part (i).
        eps_values is a list such as: [0.001, 0.005, 0.01, 0.03, ..]
        Returns the list of accuracy results [0.51, 0.78, ...] where 0.51 is the accuracy when eps = 0.001,
        0.78 is the accuracy when eps = 0.005, and so forth.
    """
    accuracies = []

    extracted_dataset = extract(dataset)
    extracted_counts = get_counts(extracted_dataset)

    correct_answer = np.argmax(extracted_counts) + 1

    for epsilon in eps_values:
        num_correct = 0

        for _ in range(1000):
            num_correct += (most_visited_exponential(extracted_dataset,
                            epsilon) == correct_answer)

        accuracies.append((num_correct / 1000) * 100)

    return accuracies


def main():
    dataset_filename = "msnbc.dat"
    dataset = read_dataset(dataset_filename)

    non_private_histogram = get_histogram(dataset)
    print("Non private histogram:", non_private_histogram)

    print("**** N EXPERIMENT RESULTS (f of Part 2) ****")
    eps = 0.01
    n_values = []

    for i in range(1, 106, 5):
        n_values.append(i)

    errors = n_experiment(dataset, n_values, eps)

    for i in range(len(n_values)):
        print("n = ", n_values[i], " error = ", errors[i])

    print("*" * 50)

    print("**** EPSILON EXPERIMENT RESULTS (g of Part 2) ****")

    n = 50
    eps_values = [0.0001, 0.001, 0.005, 0.01, 0.05, 0.1, 1.0]
    errors = epsilon_experiment(dataset, n, eps_values)

    for i in range(len(eps_values)):
        print("eps = ", eps_values[i], " error = ", errors[i])

    print("*" * 50)

    print("**** EXPONENTIAL EXPERIMENT RESULTS ****")

    eps_values = [0.001, 0.005, 0.01, 0.03, 0.05, 0.1]
    exponential_experiment_result = exponential_experiment(dataset, eps_values)

    for i in range(len(eps_values)):
        print("eps = ", eps_values[i], " accuracy = ",
              exponential_experiment_result[i])


if __name__ == "__main__":
    main()
