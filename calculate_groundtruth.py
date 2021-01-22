"""
calculate_groundtruth.py
Author: Maggie Jacoby
Date: 2021-01-21

This function reads in the raw occupancy files (one per occupant) 
and generates a full occuapncy profile for the home.
Prints occupancy profiles for each day
"""

import os
import sys
import csv
import json
import argparse
import numpy as np
import pandas as pd
from glob import glob
from datetime import datetime, timedelta

from my_functions import *



def get_date_list(read_file, H_num):

    with open(read_file) as f:
        all_homes = json.load(f)
    
    home_st = all_homes[H_num]
    all_days = []

    for st in home_st:
        start, end = st[0], st[1]
        pd_days = pd.date_range(start=start, end=end).tolist()
        days = [d.strftime('%Y-%m-%d') for d in pd_days]
        all_days.extend(days)

    return all_days



def calculate_groundtruth_df(path):

    occupant_files = glob(f'{path}/GroundTruth/*.csv')
    occupant_names = []
    occupants = {}
    
    enter_times, exit_times = [], []

    for occ in occupant_files:
        occupant_name = os.path.basename(occ).split('-')[1].strip('.csv')
        occupant_names.append(occupant_name)
        ishome = []
        with open(occ) as csv_file:
            csv_reader, line_count = csv.reader(csv_file, delimiter=','), 0
            for row in csv_reader:
                status, when = row[1], row[2].split('at')
                dt_day = datetime.strptime(str(when[0] + when[1]), '%B %d, %Y %I:%M%p')
                ishome.append((status, dt_day))
                if line_count == 0:
                    enter_times.append(dt_day)
                line_count += 1
            exit_times.append(dt_day)
        occupants[occupant_name] = ishome

    first, last = sorted(enter_times)[0], sorted(exit_times)[-1]

    occ_range = pd.date_range(start=first, end=last, freq='10S')
    occ_df = pd.DataFrame(index=occ_range)

    for occ in occupants:
        occ_df[occ] = 99
        state1 = 'exited'
        for row in occupants[occ]:
            date = row[1]
            state2 = row[0]
            occ_df.loc[(occ_df.index < date) & (occ_df[occ] == 99) & (state1 == 'exited') & (state2 == 'entered'), occ] = 0
            occ_df.loc[(occ_df.index <= date) & (occ_df[occ] == 99) & (state1 == 'entered') & (state2 == 'exited'), occ] = 1
            state1 = state2
        occ_df.loc[(occ_df.index >= date) & (occ_df[occ] == 99) & (state1 == 'exited'), occ] = 0
        occ_df.loc[(occ_df.index >= date) & (occ_df[occ] == 99) & (state1 == 'entered'), occ] = 1

    occ_df['occupied'] = occ_df[list(occupants.keys())].max(axis=1)
    occ_df.index = pd.to_datetime(occ_df.index)
    occ_df.index.name = 'timestamp'

    summary_df = occ_df.copy()
    summary_df['number'] = summary_df[list(occupants.keys())].sum(axis=1)
    summary_df = summary_df.drop(columns=list(occupants.keys()))
    summary_df = create_buffer(summary_df)
    
    return summary_df, occ_df


def create_buffer(df, buffer=5):
    num_points = buffer*6
    df['occupied'] = df['occupied'].replace(to_replace=0, value=np.nan)
    df['occupied'] = df['occupied'].fillna(method='ffill', limit=num_points)
    df['occupied'] = df['occupied'].fillna(method='bfill', limit=num_points)
    df['occupied'] = df['occupied'].fillna(value=0).astype('int32')
    return df


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Read occupancy files and generate ground truth.')
    parser.add_argument('-path','--path', default='', type=str, help='path of stored data')
    parser.add_argument('-save', '--save', default='', type=str, help='location to store calculated ground truth')

    args = parser.parse_args()

    path = args.path
    H_num = os.path.basename(path.strip('/')).split('-')[0]

    save_root = os.path.join(args.save, f'{H_num}-GROUNDTRUTH') if len(args.save) > 0 else os.path.join(path, 'Inference_DB/GroundTruth')
    save_path = make_storage_directory(save_root)

    summary_df, occ_df = calculate_groundtruth_df(path)

    occ_save_path = make_storage_directory(os.path.join(path, 'Inference_DB/Full_inferences/'))
    occ_fname = os.path.join(occ_save_path, f'{H_num}_occupancy_buffer.csv')
    occ_df.to_csv(occ_fname, index = True)

    start_end_file = 'start_end_dates.json'
    all_days = get_date_list(read_file=start_end_file, H_num=H_num)

    for day in all_days:
        day_df = summary_df.loc[day]
        fname = os.path.join(save_path, f'{day}_{H_num}_groundtruth.csv')
        day_df.to_csv(fname, index=True)









