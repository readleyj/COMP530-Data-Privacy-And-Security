from collections import Counter

import numpy as np

DOMAIN = list(range(25))


def read_dataset(filename):
    """
        Reads the dataset with given filename.

        Args:
            filename (str): Path to the dataset file
        Returns:
            Dataset rows as a list.
    """

    result = []
    with open(filename, "r") as f:
        for line in f:
            result.append(int(line))
    return result


def get_counts(dataset):
    counts = Counter(dataset)
    return [counts[hour] for hour in DOMAIN]


def calculate_average_error(actual_hist, noisy_hist):
    num_bins = len(actual_hist)

    return sum([abs(actual_val - noise_val)
                for actual_val, noise_val in zip(actual_hist, noisy_hist)]) / num_bins


def apply_estimator(hist, val, n, p, q):
    return (hist[val] - n * q) / (p - q)


def perturb_grr(val, epsilon):
    """
        Perturbs the given value using GRR protocol.

        Args:
            val (int): User's true value
            epsilon (float): Privacy parameter
        Returns:
            Perturbed value that the user reports to the server
    """
    d = len(DOMAIN)

    p = np.exp(epsilon) / (np.exp(epsilon) + d - 1)

    if np.random.uniform() < p:
        return val
    else:
        domain_without_val = [elem for elem in DOMAIN if elem != val]
        return np.random.choice(domain_without_val)


def estimate_grr(perturbed_values, epsilon):
    """
        Estimates the histogram given GRR perturbed values of the users.

        Args:
            perturbed_values (list): Perturbed values of all users
            epsilon (float): Privacy parameter
        Returns:
            Estimated histogram as a list: [1.5, 6.7, ..., 1061.0] 
            for each hour in the domain [0, 1, ..., 24] respectively.
    """
    d = len(DOMAIN)

    p = np.exp(epsilon) / (np.exp(epsilon) + d - 1)
    q = (1 - p) / (d - 1)

    n = len(perturbed_values)
    noisy_hist = get_counts(perturbed_values)

    denoised_hist = [apply_estimator(
        noisy_hist, val, n, p, q) for val in DOMAIN]

    return denoised_hist


def grr_experiment(dataset, epsilon):
    """
        Conducts the data collection experiment for GRR.

        Args:
            dataset (list): The daily_time dataset
            epsilon (float): Privacy parameter
        Returns:
            Error of the estimated histogram (float) -> Ex: 330.78
    """

    actual_hist = get_counts(dataset)

    perturbed_values = [perturb_grr(val, epsilon) for val in dataset]
    denoised_hist = estimate_grr(perturbed_values, epsilon)

    error = calculate_average_error(actual_hist, denoised_hist)

    return error


def encode_rappor(val):
    """
        Encodes the given value into a bit vector.

        Args:
            val (int): The user's true value.
        Returns:
            The encoded bit vector as a list: [0, 1, ..., 0]
    """
    return [int(val == elem) for elem in DOMAIN]


def perturb_rappor(encoded_val, epsilon):
    """
        Perturbs the given bit vector using RAPPOR protocol.

        Args:
            encoded_val (list) : User's encoded value
            epsilon (float): Privacy parameter
        Returns:
            Perturbed bit vector that the user reports to the server as a list: [1, 1, ..., 0]
    """

    p = (np.exp(epsilon / 2)) / (np.exp(epsilon / 2) + 1)

    def perturb_bit(bit):
        is_bit_preserved = np.random.uniform() < p

        return bit if is_bit_preserved else abs(1 - bit)

    perturbed_vector = [perturb_bit(bit) for bit in encoded_val]

    return perturbed_vector


def estimate_rappor(perturbed_values, epsilon):
    """
        Estimates the histogram given RAPPOR perturbed values of the users.

        Args:
            perturbed_values (list of lists): Perturbed bit vectors of all users
            epsilon (float): Privacy parameter
        Returns:
            Estimated histogram as a list: [1.5, 6.7, ..., 1061.0] 
            for each hour in the domain [0, 1, ..., 24] respectively.
    """

    p = (np.exp(epsilon / 2)) / (np.exp(epsilon / 2) + 1)
    q = 1 - p

    n = len(perturbed_values)
    noisy_hist = [sum(index_vals) for index_vals in zip(*perturbed_values)]

    denoised_hist = [apply_estimator(
        noisy_hist, val, n, p, q) for val in DOMAIN]

    return denoised_hist


def rappor_experiment(dataset, epsilon):
    """
        Conducts the data collection experiment for RAPPOR.

        Args:
            dataset (list): The daily_time dataset
            epsilon (float): Privacy parameter
        Returns:
            Error of the estimated histogram (float) -> Ex: 330.78
    """
    actual_hist = get_counts(dataset)

    encoded_values = [encode_rappor(val) for val in dataset]
    perturbed_values = [perturb_rappor(val, epsilon) for val in encoded_values]
    denoised_hist = estimate_rappor(perturbed_values, epsilon)

    error = calculate_average_error(actual_hist, denoised_hist)

    return error


def main():
    dataset = read_dataset("daily_time.txt")

    print("GRR EXPERIMENT")
    for epsilon in [0.1, 0.5, 1.0, 2.0, 4.0, 6.0]:
        error = grr_experiment(dataset, epsilon)
        print("e={}, Error: {:.2f}".format(epsilon, error))

    print("*" * 50)
    print("RAPPOR EXPERIMENT")
    for epsilon in [0.1, 0.5, 1.0, 2.0, 4.0, 6.0]:
        error = rappor_experiment(dataset, epsilon)
        print("e={}, Error: {:.2f}".format(epsilon, error))


if __name__ == "__main__":
    main()
