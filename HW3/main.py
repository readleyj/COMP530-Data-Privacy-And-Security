import copy

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.utils import shuffle

MODELS = {
    "DT": DecisionTreeClassifier(max_depth=5, random_state=0),
    "LR": LogisticRegression(penalty="l2", tol=0.001, C=0.1, max_iter=100),
    "SVC": SVC(C=0.5, kernel="poly", random_state=0),
}

LABEL_FLIPPING_NUM_RUNS = 100

EVASION_RANDOM_NOISE_VARIANCE = 1.5

BACKDOOR_TRIGGER_FLAG = 1000
BACKDOOR_NUM_FLAGGED_FEATURES = 2
BACKDOOR_RANDOM_NOISE_VARIANCE = 5.0
BACKDOOR_NUM_TEST_SAMPLES = 1000


def generate_backdoored_samples(num_samples, num_features):
    backdoored_x_samples = []
    backdoored_y_samples = np.ones(num_samples)

    for _ in range(num_samples):
        sample = np.random.normal(0, BACKDOOR_RANDOM_NOISE_VARIANCE, num_features)
        sample[:BACKDOOR_NUM_FLAGGED_FEATURES] = BACKDOOR_TRIGGER_FLAG

        backdoored_x_samples.append(sample)

    backdoored_x_samples = np.reshape(backdoored_x_samples, (-1, num_features))

    return backdoored_x_samples, backdoored_y_samples


def attack_label_flipping(X_train, X_test, y_train, y_test, model_type, n):
    model = MODELS[model_type]

    num_instances = len(X_train)
    num_to_flip = int(n * num_instances)

    running_accuracy = 0.0

    for _ in range(LABEL_FLIPPING_NUM_RUNS):
        X_train, y_train = shuffle(X_train, y_train)

        y_train[:num_to_flip] = np.absolute(
            np.ones_like(num_to_flip) - y_train[:num_to_flip]
        )

        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)

        running_accuracy += accuracy

    return running_accuracy / LABEL_FLIPPING_NUM_RUNS


def backdoor_attack(X_train, y_train, model_type, num_samples):
    model = MODELS[model_type]
    num_features = np.shape(X_train)[1]

    backdoored_X_train = copy.deepcopy(X_train)
    backdoored_y_train = copy.deepcopy(y_train)

    backdoored_x_samples, backdoored_y_samples = generate_backdoored_samples(
        num_samples, num_features
    )

    backdoored_X_train = np.append(backdoored_X_train, backdoored_x_samples, axis=0)
    backdoored_y_train = np.append(backdoored_y_train, backdoored_y_samples, axis=0)

    backdoored_model = model.fit(backdoored_X_train, backdoored_y_train)

    backdoored_X_test, backdoored_y_test = generate_backdoored_samples(
        BACKDOOR_NUM_TEST_SAMPLES, num_features
    )

    predictions = backdoored_model.predict(backdoored_X_test)
    accuracy = accuracy_score(backdoored_y_test, predictions)

    return accuracy


def evade_model(trained_model, actual_example):
    actual_class = trained_model.predict([actual_example])[0]
    modified_example = copy.deepcopy(actual_example)
    pred_class = actual_class

    num_features = len(actual_example)

    while pred_class == actual_class:
        rand_idx = np.random.choice(range(num_features))
        modified_example[rand_idx] = np.random.normal(
            actual_example[rand_idx], EVASION_RANDOM_NOISE_VARIANCE
        )

        pred_class = trained_model.predict([modified_example])[0]

    return modified_example


def calc_perturbation(actual_example, adversarial_example):
    if len(actual_example) != len(adversarial_example):
        print("Number of features is different, cannot calculate perturbation amount.")
        return -999
    else:
        tot = 0.0
        for i in range(len(actual_example)):
            tot = tot + abs(actual_example[i] - adversarial_example[i])
        return tot / len(actual_example)


def evaluate_transferability(DTmodel, LRmodel, SVCmodel, actual_examples):
    original_models = [("DT", DTmodel), ("LR", LRmodel), ("SVC", SVCmodel)]
    num_examples = len(actual_examples)

    total_successful_transfers = 0
    num_model_pairs_evaluated = 0

    for original_model_name, original_model in original_models:
        secondary_models = [
            (model_name, model)
            for (model_name, model) in original_models
            if model_name != original_model_name
        ]

        adversarial_examples = [
            evade_model(original_model, example) for example in actual_examples
        ]
        original_model_predictions = original_model.predict(adversarial_examples)

        for secondary_model_name, secondary_model in secondary_models:
            secondary_model_predictions = secondary_model.predict(adversarial_examples)

            num_successful_transfers = sum(
                [
                    int(original_model_pred == secondary_model_pred)
                    for (original_model_pred, secondary_model_pred) in zip(
                        original_model_predictions, secondary_model_predictions
                    )
                ]
            )

            total_successful_transfers += num_successful_transfers
            num_model_pairs_evaluated += 1

            print(
                f"{num_successful_transfers} examples out of {num_examples} transferred from {original_model_name} to {secondary_model_name}"
            )

        transferability_metric = total_successful_transfers / num_model_pairs_evaluated

        print(
            f"Cross-model transferability of evasion attack is {transferability_metric}"
        )


def steal_model(remote_model, model_type, examples):
    remote_model_responses = remote_model.predict(examples)

    stolen_model = MODELS[model_type]
    stolen_model.fit(examples, remote_model_responses)

    return stolen_model


def main():
    data_filename = "BankNote_Authentication.csv"
    features = ["variance", "skewness", "curtosis", "entropy"]

    df = pd.read_csv(data_filename)
    df = df.dropna(axis=0, how="any")
    y = df["class"].values
    y = LabelEncoder().fit_transform(y)
    X = df[features].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=0
    )

    # Model 1: Decision Tree
    myDEC = DecisionTreeClassifier(max_depth=5, random_state=0)
    myDEC.fit(X_train, y_train)
    DEC_predict = myDEC.predict(X_test)
    print("Accuracy of decision tree: " + str(accuracy_score(y_test, DEC_predict)))

    # Model 2: Logistic Regression
    myLR = LogisticRegression(penalty="l2", tol=0.001, C=0.1, max_iter=100)
    myLR.fit(X_train, y_train)
    LR_predict = myLR.predict(X_test)
    print("Accuracy of logistic regression: " + str(accuracy_score(y_test, LR_predict)))

    # Model 3: Support Vector Classifier
    mySVC = SVC(C=0.5, kernel="poly", random_state=0)
    mySVC.fit(X_train, y_train)
    SVC_predict = mySVC.predict(X_test)
    print("Accuracy of SVC: " + str(accuracy_score(y_test, SVC_predict)))

    # Label flipping attack executions:
    model_types = ["DT", "LR", "SVC"]
    n_vals = [0.05, 0.10, 0.20, 0.40]
    for model_type in model_types:
        for n in n_vals:
            acc = attack_label_flipping(X_train, X_test, y_train, y_test, model_type, n)
            print("Accuracy of poisoned", model_type, str(n), ":", acc)

    # Backdoor attack executions:
    counts = [0, 1, 3, 5, 10]
    for model_type in model_types:
        for num_samples in counts:
            success_rate = backdoor_attack(X_train, y_train, model_type, num_samples)
            print(
                "Success rate of backdoor:",
                success_rate,
                "model_type:",
                model_type,
                "num_samples:",
                num_samples,
            )

    # Evasion attack executions:
    trained_models = [myDEC, myLR, mySVC]
    num_examples = 50
    total_perturb = 0.0
    for trained_model in trained_models:
        for i in range(num_examples):
            actual_example = X_test[i]
            adversarial_example = evade_model(trained_model, actual_example)
            if (
                trained_model.predict([actual_example])[0]
                == trained_model.predict([adversarial_example])[0]
            ):
                print("Evasion attack not successful! Check function: evade_model.")
            perturbation_amount = calc_perturbation(actual_example, adversarial_example)
            total_perturb = total_perturb + perturbation_amount
    print("Avg perturbation for evasion attack:", total_perturb / num_examples)

    # Transferability of evasion attacks:
    trained_models = [myDEC, myLR, mySVC]
    num_examples = 100
    evaluate_transferability(
        myDEC, myLR, mySVC, X_test[num_examples : num_examples * 2]
    )

    # Model stealing:
    budgets = [5, 10, 20, 30, 50, 100, 200]
    for n in budgets:
        print("******************************")
        print("Number of queries used in model stealing attack:", n)
        stolen_DT = steal_model(myDEC, "DT", X_test[0:n])
        stolen_predict = stolen_DT.predict(X_test)
        print("Accuracy of stolen DT: " + str(accuracy_score(y_test, stolen_predict)))
        stolen_LR = steal_model(myLR, "LR", X_test[0:n])
        stolen_predict = stolen_LR.predict(X_test)
        print("Accuracy of stolen LR: " + str(accuracy_score(y_test, stolen_predict)))
        stolen_SVC = steal_model(mySVC, "SVC", X_test[0:n])
        stolen_predict = stolen_SVC.predict(X_test)
        print("Accuracy of stolen SVC: " + str(accuracy_score(y_test, stolen_predict)))


if __name__ == "__main__":
    main()
