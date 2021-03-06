#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 06/06/2019

@author: Simone Boglio
"""

import os
import numpy as np
from Data_manager.IncrementalSparseMatrix import IncrementalSparseMatrix

from Data_manager.Movielens.Movielens1MReader import Movielens1MReader as Movielens1MReader_DataManager
from Data_manager.split_functions.split_data_on_timestamp import split_data_on_timestamp
from Data_manager.load_and_save_data import save_data_dict_zip, load_data_dict_zip
from Data_manager.Utility import print_stat_datareader
from Conferences.IJCAI.DELF_our_interface.Dataset import Dataset as Dataset_github


class Movielens1MReader:

    DATASET_NAME = "Movielens1M"

    URM_DICT = {}
    ICM_DICT = {}

    def __init__(self, pre_splitted_path, type = "original"):

        pre_splitted_path += "data_split/"
        pre_splitted_filename = "splitted_data_"

        # If directory does not exist, create
        if not os.path.exists(pre_splitted_path):
            os.makedirs(pre_splitted_path)

        try:
            print("Dataset_{}: Attempting to load pre-splitted data".format(self.DATASET_NAME))

            for attrib_name, attrib_object in load_data_dict_zip(pre_splitted_path, pre_splitted_filename).items():
                self.__setattr__(attrib_name, attrib_object)


        except FileNotFoundError:

            print("Dataset_{}: Pre-splitted data not found, building new one".format(self.DATASET_NAME))

            if type == "original":

                # Ensure file is loaded as matrix
                Dataset_github.load_rating_file_as_list = Dataset_github.load_rating_file_as_matrix

                dataset = Dataset_github("Conferences/IJCAI/DELF_original/Data/ml-1m")

                URM_train, URM_validation, URM_test, testNegatives = dataset.trainMatrix, dataset.validRatings, \
                                                                     dataset.testRatings, dataset.testNegatives

                URM_train = URM_train.tocsr()
                URM_validation = URM_validation.tocsr()
                URM_test = URM_test.tocsr()
                URM_timestamp = "no"


                from Base.Recommender_utils import reshapeSparse


                shape = (max(URM_train.shape[0], URM_validation.shape[0], URM_test.shape[0]),
                         max(URM_train.shape[1], URM_validation.shape[1], URM_test.shape[1]))


                URM_train = reshapeSparse(URM_train, shape)
                URM_validation = reshapeSparse(URM_validation, shape)
                URM_test = reshapeSparse(URM_test, shape)


                URM_test_negatives_builder = IncrementalSparseMatrix(n_rows=shape[0], n_cols=shape[1])

                for user_index in range(len(dataset.testNegatives)):

                    user_test_items = dataset.testNegatives[user_index]

                    URM_test_negatives_builder.add_single_row(user_index, user_test_items, data=1.0)


                URM_test_negative = URM_test_negatives_builder.get_SparseMatrix()


            elif type == "ours":

                # create from full dataset with leave out one time wise from ORIGINAL full dateset
                data_reader = Movielens1MReader_DataManager()
                loaded_dataset = data_reader.load_data()

                URM_all = loaded_dataset.get_URM_from_name("URM_all")
                URM_timestamp = loaded_dataset.get_URM_from_name("URM_timestamp")

                # make rating implicit
                URM_all.data = np.ones_like(URM_all.data)

                URM_train, URM_validation, URM_test, URM_test_negative = split_data_on_timestamp(URM_all, URM_timestamp, negative_items_per_positive=99)

            else:
                assert False


            self.URM_DICT = {
                "URM_train": URM_train,
                "URM_test": URM_test,
                "URM_validation": URM_validation,
                "URM_test_negative": URM_test_negative,
                "URM_timestamp": URM_timestamp,
            }


            save_data_dict_zip(self.URM_DICT, self.ICM_DICT, pre_splitted_path, pre_splitted_filename)


        print("{}: Dataset loaded".format(self.DATASET_NAME))

        print_stat_datareader(self)
