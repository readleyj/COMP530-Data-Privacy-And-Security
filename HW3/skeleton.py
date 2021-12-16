import sys
import random

import numpy as np
import pandas as pd
import copy

from collections import Counter

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC


###############################################################################
############################### Label Flipping ################################
###############################################################################


def attack_label_flipping(X_train, X_test, y_train, y_test, model_type, n):
    # TODO: You need to implement this function!
    # You may want to use copy.deepcopy() if you will modify data
    return -999


###############################################################################
################################## Backdoor ###################################
###############################################################################


def backdoor_attack(X_train, y_train, model_type, num_samples):
    # TODO: You need to implement this function!
    # You may want to use copy.deepcopy() if you will modify data
    return -999


###############################################################################
############################## Evasion ########################################
###############################################################################


def evade_model(trained_model, actual_example):
    # TODO: You need to implement this function!
    actual_class = trained_model.predict([actual_example])[0]
    modified_example = copy.deepcopy(actual_example)
    # while pred_class == actual_class:
    # do something to modify the instance
    #    print("do something")
    modified_example[0] = -2.0
    return modified_example


def calc_perturbation(actual_example, adversarial_example):
    # You do not need to modify this function.
    if len(actual_example) != len(adversarial_example):
        print("Number of features is different, cannot calculate perturbation amount.")
        return -999
    else:
        tot = 0.0
        for i in range(len(actual_example)):
            tot = tot + abs(actual_example[i] - adversarial_example[i])
        return tot / len(actual_example)


###############################################################################
############################## Transferability ################################
###############################################################################


def evaluate_transferability(DTmodel, LRmodel, SVCmodel, actual_examples):
    # TODO: You need to implement this function!
    print(
        "Here, you need to conduct some experiments related to transferability and print their results..."
    )


###############################################################################
########################## Model Stealing #####################################
###############################################################################


def steal_model(remote_model, model_type, examples):
    # TODO: You need to implement this function!
    # This function should return the STOLEN model, but currently it returns the remote model
    # You should change the return value once you have implemented your model stealing attack
    return remote_model


###############################################################################
############################### Main ##########################################
###############################################################################

## DO NOT MODIFY CODE BELOW THIS LINE. FEATURES, TRAIN/TEST SPLIT SIZES, ETC. SHOULD STAY THIS WAY. ##
## JUST COMMENT OR UNCOMMENT PARTS YOU NEED. ##


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
