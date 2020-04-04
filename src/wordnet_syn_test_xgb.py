import pandas as pd
import numpy as np
from lr.text_processing.util import pre_process_nli_df
from lr.training.util import get_ternary_label, filter_df_by_label
from lr.text_processing.transformations.wordnet import path_base_transformation
from lr.text_processing.transformations.wordnet import path_base_transformation_p
from lr.text_processing.transformations.wordnet import path_base_transformation_h
from lr.training.language_representation import Tfidf
from lr.models.xgb import XGBCWrapper
from lr.stats.h_testing import LIMts_test
from IPython.display import display, HTML
from sklearn.exceptions import ConvergenceWarning
import warnings
import os
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# params


def wordsyn_test(transformation_type, max_features, cv,
                 n_jobs, n_iter, rho, M, E, S,
                 verbose, random_state_list,
                 dgp_seed_list, output_dir):


    random_state_list_str = map(lambda x: str(x), random_state_list) 
    results_path = "results/snli/xgb/sin_p_h/rho_{:.2f}_random_state_{}".format(rho, "_".join(random_state_list_str))
    results_path = results_path.replace(".", "p")
    results_path = results_path + ".csv"

    # Loading data

    train_path = "data/snli/train.csv"
    dev_path = "data/snli/dev.csv"

    train = pd.read_csv(train_path)
    dev = pd.read_csv(dev_path)
    train = filter_df_by_label(train.dropna()).reset_index(drop=True)
    dev = filter_df_by_label(dev.dropna()).reset_index(drop=True)

    pre_process_nli_df(train)
    pre_process_nli_df(dev)

    # creating transformation function

    train_path_mod = "data/snli/train_p_h_syn_noun.csv"
    dev_path_mod = "data/snli/dev_p_h_syn_noun.csv"

    if transformation_type == "p_h":
        def train_trans(df): return path_base_transformation(
            df, train_path_mod)

        def dev_trans(df): return path_base_transformation(df, dev_path_mod)

        transformation_name = "wordnet sin tranformation p and h"

    elif transformation_type == "only_p":
        def train_trans(df): return path_base_transformation_p(
            df, train_path_mod)

        def dev_trans(df): return path_base_transformation_p(df, dev_path_mod)

        transformation_name = "wordnet sin tranformation p only"

    elif transformation_type == "only_h":
        def train_trans(df): return path_base_transformation_h(
            df, train_path_mod)

        def dev_trans(df): return path_base_transformation_h(df, dev_path_mod)

        transformation_name = "wordnet sin tranformation h only"

    else:
        exit()

    dev_t = dev_trans(dev)

    # hyperparms for the XGB models
    param_grid = {'n_estimators': range(10, 20, 5),
                  'max_depth': range(2, 11),
                  "reg_alpha": np.arange(0.05, 1.05, 0.05),
                  "reg_gamma": np.arange(0.05, 1.05, 0.05),
                  "learning_rate": np.arange(0.05, 1.05, 0.05),
                  "subsample": np.arange(0.05, 1.05, 0.05),
                  "colsample_bytree": np.arange(0.05, 1.05, 0.05)}


    hyperparams = {"RepresentationFunction": Tfidf,
                   "cv": cv,
                   "random_state": None,
                   "verbose": verbose,
                   "n_jobs": n_jobs,
                   "n_iter": n_iter,
                   "max_features": max_features,
                   "label_translation": get_ternary_label,
                   "param_grid": param_grid,
                   "random_state_list": random_state_list,
                   "dgp_seed_list": dgp_seed_list,
                   "data_set_name": "snli",
                   "transformation_name": transformation_name,
                   "rho": rho,
                   "model_name_or_path": "gradient boosting",
                   "number_of_samples": M,
                   "number_of_models": E,
                   "number_of_simulations": S,
                    "output_dir": output_dir,
                   "verbose": verbose}

    # performing the tests
    results = LIMts_test(train=train,
                         dev=dev,
                         train_transformation=train_trans,
                         dev_transformation=dev_trans,
                         Model=XGBCWrapper,
                         hyperparams=hyperparams)

    # saving results

    results.to_csv(results_path, index=False)


if __name__ == '__main__':

    debug = False

    pcts = [0.0, 0.25, 0.5, 0.75, 1.0]

    random_states_list_list = [[127842, 13943],
                                [14193, 1813],
                                [1149, 1272],
                                [13202, 165],
                                [1715, 1766],
                                [1587, 1590],
                                [1311, 1523]]  # random states for  p_h




    dgp_seed_list_list = [[12456, 1548],
                           [12647, 1377],
                           [1242, 1431],
                           [1192, 1716],
                           [14571, 18152],
                           [134552, 15656],
                           [15523, 133737]]  # dgp states for p_h



    M = 2
    E = 1
    S = 1000
    n_jobs = 8 
    n_iter = 1
    cv = 5
    transformation_type = "p_h"

    for rho, random_state_list, dgp_seed_list in zip(
            pcts, random_states_list_list, dgp_seed_list_list):

        output_dir = "xgb_{}_{}".format(transformation_type, rho)
        output_dir = output_dir.replace(".", "p")

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        print("\nPerforming tests for rho = {:.1%}\n".format(rho))

        wordsyn_test(transformation_type=transformation_type,
                     max_features=None,
                     cv=cv,
                     n_jobs=n_jobs,
                     n_iter=n_iter,
                     rho=rho,
                     M=M,
                     E=E,
                     S=S,
                     verbose=True,
                     random_state_list=random_state_list,
                     dgp_seed_list=dgp_seed_list,
                     output_dir=output_dir)

        params_keys = ['n_estimators', 'max_depth', "reg_alpha",
               "reg_gamma", "learning_rate", "subsample", "colsample_bytree"]

# hyperparams = {"RepresentationFunction": Tfidf,
#                "random_state": 34,
#                "verbose": verbose,
#                "n_jobs": n_jobs,
#                "max_features": max_features,
#                "label_translation": get_ternary_label,
#                "dgp_seed": 34,
#                "data_set_name": "snli",
#                "transformation_name": None,
#                "rho": 0.3,
#                "model_name_or_path": "gradient boosting",
#                "number_of_simulations": 10000,
#                 "output_dir": None,
#                "verbose": verbose}
               
# for k in params_keys:
#     hyperparams[k] = search_results.loc[0,k]
    
    
# m = XGBCWrapper(hyperparams)
# m.fit(train)
# model.get_acc(dev)