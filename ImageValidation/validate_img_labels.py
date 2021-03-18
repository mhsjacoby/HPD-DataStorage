"""
validate_img_labels.py
Author: Maggie Jacoby
Date: 2021-03-01
"""

import os
import sys
import csv
import yaml
import pickle
import logging
import argparse
import numpy as np
import pandas as pd
from glob import glob
from datetime import datetime, date



def get_difference(title, val):

        predicted = pd.read_csv(os.path.join(summary_path, f'{hub_num}_{title}.csv'), index_col='timestamp')
        predicted.index = pd.to_datetime(predicted.index)
        
        images = sorted(glob(os.path.join(hub, title.capitalize(), f'*_{hub_num}_{H_num}.png')))
        img_times = [(os.path.basename(f).split('_')[:2]) for f in images]
        img_times = [datetime.strptime(f'{f[0]}_{f[1]}', '%Y-%m-%d_%H%M%S') for f in img_times]
        
        actual = pd.DataFrame(val, index=img_times, columns=['ground truth'])
        misclassified = list(set(actual.index) - set(predicted.index))

        return misclassified, actual, predicted



"""
actual (P, N): timestamp, 0/1
predicted: timestamp, occupied (0/1), probability
misclassified: timestamp 
"""


labelspath = '/Users/maggie/Desktop/ImageLabeling/Labeled_Images_from_Jasmine/'
summaries = os.path.join(labelspath, 'As_Labeled_Summaries')

homes = sorted(glob(os.path.join(labelspath, 'H*' )))


for home in homes:
    H_num = os.path.basename(home)
    hubs = sorted(glob(os.path.join(home, '*S*')))
    hubs_summary = {}
    for hub in hubs:
        
        hub_num = os.path.basename(hub)
        summary_path = os.path.join(summaries, f'{H_num}_Summaries')
        print(hub_num)
        FN, P, predicted_occ = get_difference(title='occupied', val=1)
        FP, N, predicted_vac = get_difference(title='vacant', val=0)

        full_df = pd.concat([predicted_occ, predicted_vac], axis=0)
        full_df.rename({'occupied':'predicted'}, axis='columns', inplace=True)
        full_df['actual'] = 0
        full_df.loc[full_df.index.isin(P.index), 'actual'] = 1  
        full_df = full_df.sort_index()
        # print((full_df))
        save_path = os.path.join(labelspath, 'True_Summaries', H_num)
        os.makedirs(save_path, exist_ok=True)
        full_df.to_csv(os.path.join(save_path, f'{H_num}_{hub_num}_labels.csv'), index='timestamp')
        hubs_summary[hub_num] = {'fp' : len(FP), 'tp': len(P)-len(FN), 'fn': len(FN), 'tn': len(N)-len(FP) }
    summary_df = pd.DataFrame(hubs_summary)
    summary_df = summary_df.transpose()
    summary_df.index.name = 'hub'
    summary_df.to_csv(os.path.join(labelspath, 'True_Summaries', f'{H_num}_metrics.csv'), index='hub')

