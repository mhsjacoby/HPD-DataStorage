"""
count_all_modalities.py
Author: Maggie Jacoby
date: 2021-01-13

modifications for looking H2, which was saved differently (already in database format)

"""

import os
import csv
import sys
from glob import glob
import numpy as np
import pandas as pd
from datetime import datetime

from my_functions import *


### Populate dictionary with all days used in database
start_end_dict = {
    'H1': [['2019-11-26',' 2019-12-25']], 
    'H2': [['2019-03-13', '2019-03-29']], 
    # 'H2': [['2019-03-13', '2019-03-15']], # smaller subset for testing 
    'H3': [['2019-07-23', '2019-08-04'], ['2019-08-15', '2019-09-05']], 
    'H4': [['2019-05-01', '2019-05-12'], ['2019-05-17', '2019-05-21']],
    'H5': [['2019-06-07', '2019-06-21']],
    'H6': [['2019-10-12', '2019-11-02'], ['2019-11-20', '2019-12-05']]}

def database_days():
    all_days_dict = {}

    for home in start_end_dict:
        home_st = start_end_dict[home]
        all_days = []

        for st in home_st:
            start, end = st[0], st[1]
            pd_days = pd.date_range(start=start, end=end).tolist()
            days = [d.strftime('%Y-%m-%d') for d in pd_days]
            all_days.extend(days)
        all_days_dict[home] = all_days
    
    return all_days_dict

################

def count_audio(days_to_use, data_path, hub=None, max_files=8640):
    print(f'Counting audio on {hub}...')

    data_path = os.path.join(data_path, f'{H_num}-{hub}-audio')
    dates = glob(os.path.join(data_path, '2019-*'))
    dates = [f for f in dates if os.path.basename(f) in days_to_use]
    print(hub, 'audio', len(dates))

    counts = {}
    for day in dates:
        all_times = glob(os.path.join(day, '*/*.csv'))
        set_times = set([os.path.basename(x).split('_')[1] for x in all_times])
        dt = datetime.strptime(os.path.basename(day), '%Y-%m-%d').date()
        totals = len(set_times)/max_files
        counts[dt] = float(f'{totals:.2}') if totals != 0 else 0.0

    return counts

def count_images(days_to_use, data_path, hub=None, max_files=86400):
    print(f'Counting images on {hub}...')

    data_path = os.path.join(data_path, f'{H_num}-{hub}-images')
    dates = glob(os.path.join(data_path, '2019-*'))
    dates = [f for f in dates if os.path.basename(f) in days_to_use]
    print(hub, 'img', len(dates))

    counts = {}
    for day in dates:
        all_times = glob(os.path.join(day, '*/*.png'))
        set_times = set([os.path.basename(x).split('_')[1] for x in all_times])
        dt = datetime.strptime(os.path.basename(day), '%Y-%m-%d').date()
        totals = len(set_times)/max_files
        counts[dt] = float(f'{totals:.2}') if totals != 0 else 0.0

    return counts

def read_dark(days_to_use, data_path, hub, max_files=86400):

    img_csv_summary = glob(f'/Volumes/TOSHIBA-22/H2-red/Summaries/H2-{hub}-img-summary.txt')[0]
    summary_df = pd.read_csv(img_csv_summary, delimiter=' ', usecols=['day', '%Dark'], index_col='day')
    df_dict = summary_df.to_dict()
    df_dates, df_perc = df_dict['%Dark'].keys(), df_dict['%Dark'].values()
    dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in df_dates]
    counts = {d: p for d, p in zip(dates, df_perc) if d.strftime('%Y-%m-%d') in days_to_use}
    
    return counts


def count_env(days_to_use, data_path, hub=None, max_seconds=8640):
    print(f'Counting environmental on {hub}...')
    
    data_path = os.path.join(data_path, f'{H_num}-{hub}-env')
    dates = glob(os.path.join(data_path, '*_2019-*'))
    dates = [f for f in dates if os.path.basename(f).split('_')[2].strip('.csv') in days_to_use]
    print(hub, 'env', len(dates))

    counts = {}
    for day in dates:
        cols_to_read = ['timestamp', 'tvoc_ppb', 'temp_c', 'rh_percent', 'light_lux', 'co2eq_ppm', 'dist_mm']
        day_data = pd.read_csv(day, usecols=cols_to_read, index_col='timestamp')
        # complete_data = day_data.dropna(axis=0, how='all')
        complete_data = day_data.dropna(axis=0, how='any')
        dt = datetime.strptime(os.path.basename(day).split('_')[2].strip('.csv'), '%Y-%m-%d').date()
        totals = len(complete_data)/max_seconds
        counts[dt] = float(f'{totals:.2}') if totals != 0 else 0.0

    return counts



def count_occ(days_to_use, data_path, max_seconds=8640):
    
    dates = glob(os.path.join(data_path, '*_groundtruth.csv'))
    dates = [f for f in dates if os.path.basename(f).split('_')[0] in days_to_use]
    print(f'Counting occupancy for {len(dates)} days')

    counts = {}
    for day in dates:
        cols_to_read = ['timestamp', 'occupied']
        day_data = pd.read_csv(day, usecols=cols_to_read, index_col='timestamp')
        dt = datetime.strptime(os.path.basename(day).split('_')[0], '%Y-%m-%d').date()
        occ_df = day_data.loc[day_data.occupied == 1]
        totals = len(occ_df)/max_seconds
        counts[dt] = float(f'{totals:.2}') if totals != 0 else 0.0

    occ_counts = {'Occupancy': counts}
    occ_counts_df = pd.DataFrame(occ_counts)    
    print(occ_counts_df)

    return occ_counts_df





def get_count_df(mod_name, mod_lookup, sub_path=None):
    counts = {}
    for hub in hubs[:]:
        data_path = os.path.join(path, 'hpdmobile_dataset', sub_path)
        counts[f'{hub}_{mod_name}'] = mod_lookup(days_to_use=all_days, data_path=data_path, hub=hub)
    df = pd.DataFrame(counts)
    return df




if __name__ == '__main__':

    path = '/Volumes/TOSHIBA-22'
    H_num = 'H2'
    hubs = ['RS1', 'RS2', 'RS4', 'RS5']

    all_days = database_days()[H_num]

    # start_end_file = 'start_end_dates.json'
    # all_days = get_date_list(read_file=start_end_file, H_num=H_num)
    
    print(f'{H_num}: {len(all_days)} days')

    dark_counts = get_count_df(sub_path=' ', mod_name='Img_dark', mod_lookup=read_dark)
    env_counts = get_count_df(sub_path='H2-ENVIRONMENTAL', mod_name='Env', mod_lookup=count_env)
    audio_counts = get_count_df(sub_path='H2-AUDIO', mod_name='Audio', mod_lookup=count_audio)
    image_counts = get_count_df(sub_path='H2-IMAGES', mod_name='Img', mod_lookup=count_images)
    print('Done counting.')

    combined_img = pd.DataFrame()
    for col1, col2 in zip(sorted(image_counts.columns), sorted(dark_counts.columns)):
        if col1.split('_')[0] != col2.split('_')[0]:
            print(f'mismatch! Can not combine {col1} and {col2}')
            continue
        combined_img[col1] = image_counts[col1] + dark_counts[col2]

    
    # env_counts.to_csv(f'~/Desktop/{H_num}_env_df_counts.csv')
    # image_counts.to_csv(f'~/Desktop/{H_num}_image_df_counts.csv')
    # audio_counts.to_csv(f'~/Desktop/{H_num}_audio_df_counts.csv')
    # dark_counts.to_csv(f'~/Desktop/{H_num}_dark_df_counts.csv')

    full_counts = pd.concat([combined_img, dark_counts, env_counts, audio_counts], axis=1)
    full_counts = full_counts.reindex(sorted(full_counts.columns), axis=1)

    full_counts.to_excel(f'~/Desktop/CompleteSummaries/new_summary_code/{H_num}_counts.xlsx')


