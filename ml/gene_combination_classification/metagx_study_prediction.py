import os
import numpy as np
import random
import math
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold
import pandas as pd
from gene_combination_generator import CombinationsGenerator
from utils import *
import json


# metagx_data = pd.read_csv('/mnt/fileserver/shared/datasets/biodata/MetaGX/metaGXcovarTable.csv')
# print(metagx_data.shape)
# studies = metagx_data['study']
# print(studies[8000:9000])
#
# d = dict.fromkeys(studies.tolist())
# for kv, i in zip(d.items(), range(len(d))):
#     d[kv[0]] = i
# print(d)
# print(len(d))
#
# with open("metagx_study_labels.json", "w") as fp:
#     json.dump(d, fp)


def convert_study(val):
    d = json.loads(open('metagx_study_labels.json').read())
    return d[val]


metagx_covar_data_converted = pd.read_csv('/mnt/fileserver/shared/datasets/biodata/MetaGX/metaGXcovarTable.csv', converters=dict(study = convert_study))
studies = metagx_covar_data_converted['study']
print(studies[8000:9000])

metagx_expr_data = pd.read_csv('/mnt/fileserver/shared/datasets/biodata/MetaGX/mergedBases/noNormMergedAnd10k.csv')
print(metagx_expr_data.shape)

metagx_result_data = pd.merge(metagx_covar_data_converted, metagx_expr_data, on='sample_name')
print(metagx_result_data.shape)

y_ = metagx_result_data['study'].to_numpy()
print(y_)
cols_to_drop = metagx_result_data.iloc[:, 0:29]
X_ = metagx_result_data.drop(columns=cols_to_drop).to_numpy()
print(metagx_result_data.drop(columns=cols_to_drop).shape)
print(metagx_result_data.drop(columns=cols_to_drop).iloc[:, 0])

def calc_results_for_fold(X, y, train_index, test_index, clf):
    X_train, X_test = X[train_index], X[test_index]
    y_train, y_test = y[train_index], y[test_index]

    # clf = XGBClassifier()
    clf.fit(X_train, y_train)

    y_true_prob = clf.predict_proba(X_test)[:, 1]
    y_true = clf.predict(X_test)

    acc = np.mean(y_true == y_test)
    # auc_1 = roc_auc_score(y_test, y_true_prob)
    # auc_2 = roc_auc_score(y_test, y_true)

    return acc


# clf1 = XGBClassifier()
# n_splits = 20
# kf = KFold(n_splits=n_splits, shuffle=True)
# for i, (train_index, test_index) in enumerate(kf.split(X_)):
#     acc_f = calc_results_for_fold(X_, y_, train_index, test_index, clf1)
#     print("full: ", acc_f)


