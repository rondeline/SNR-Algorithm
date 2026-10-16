import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import re
import argparse
from typing import List
import subprocess
import json
from datetime import datetime

# Define the file path
# file_path = r"Y:\Research Projects\NIH CI study\LENA\Noise, SNRS output\Individual_SNR_Power_NIH.xlsx"
# file_path = "/Volumes/benitezbarre/Research Projects/NIH CI study/LENA/Noise, SNRS output/Individual_SNR_Power_NIH.xlsx"

def parse_subject_range(subject_input: str) -> List[str]:
    """Parse subject input which can be individual subjects or ranges.
    
    Examples:
        'S1' -> ['S1']
        'S1,S5,S10' -> ['S1', 'S5', 'S10']
        'S1-S5' -> ['S1', 'S2', 'S3', 'S4', 'S5']
        'S1-S3,S10,S15-S17' -> ['S1', 'S2', 'S3', 'S10', 'S15', 'S16', 'S17']
    """
    if not subject_input:
        return []
    
    subjects = []
    parts = subject_input.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part and part.count('-') == 1:
            # Handle range like S1-S5
            start_str, end_str = part.split('-')
            start_str = start_str.strip()
            end_str = end_str.strip()
            
            # Extract numbers
            if start_str.startswith('S') and end_str.startswith('S'):
                try:
                    start_num = int(start_str[1:])
                    end_num = int(end_str[1:])
                    
                    if start_num <= end_num:
                        for i in range(start_num, end_num + 1):
                            subjects.append(f'S{i}')
                    else:
                        print(f"Warning: Invalid range {part} (start > end)")
                except ValueError:
                    print(f"Warning: Invalid subject format in range {part}")
            else:
                print(f"Warning: Invalid subject format in range {part}")
        else:
            # Handle individual subject
            if part.startswith('S'):
                subjects.append(part)
            else:
                print(f"Warning: Invalid subject format {part}")
    
    return subjects


def filter_subjects_by_target(subject_info_df, target_subjects):
    print(subject_info_df)
    """Filter subject_info_df to only include target subjects and return relevant groups"""
    if not target_subjects:
        return subject_info_df, None
    
    # Extract just the subject prefix (e.g., 'S1' from 'S1_AA')
    subject_info_df['Subject_Prefix'] = subject_info_df['Subject_Number'].str.extract(r'(S\d+)')
    print(subject_info_df['Subject_Prefix'])
    print(target_subjects)
    
    # Filter based on the prefix
    filtered_df = subject_info_df[subject_info_df['Subject_Prefix'].isin(target_subjects)]
    
    if filtered_df.empty:
        print(f"Warning: None of the specified subjects found: {target_subjects}")
        available_subjects = subject_info_df['Subject_Prefix'].unique().tolist()
        print(f"Available subjects: {available_subjects}")
        return pd.DataFrame(), None
    
    target_groups = set()
    for _, row in filtered_df.iterrows():
        group = str(row['Group']).strip()
        subgroup = str(row['Subgroup']).strip() if pd.notna(row['Subgroup']) else 'NA'
        target_groups.add((group, subgroup))
    
    ha_ci_subjects = filtered_df[filtered_df['Subgroup'].str.strip().isin(['HA', 'CI'])]
    if not ha_ci_subjects.empty:
        target_groups.add(('HL', 'HA + CI'))
    
    target_groups.add(('ALL', 'all_subjects'))
    
    found_subjects = filtered_df['Subject_Prefix'].unique().tolist()
    print(f"Processing subjects: {found_subjects}")
    
    return filtered_df, target_groups

def make_histogram(excel_file, name_list, day_list, group, subgroup):

    excel_columns = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
        'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
        'U', 'V', 'W', 'X', 'Y', 'Z', 'AA', 'AB', 'AC', 'AD', 
        'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK', 'AL', 'AM', 
        'AN', 'AO', 'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AV', 
        'AW', 'AX', 'AY', 'AZ', 'BA', 'BB', 'BC', 'BD', 'BE', 
        'BF', 'BG', 'BH', 'BI', 'BJ', 'BK', 'BL', 'BM', 'BN', 
        'BO', 'BP', 'BQ', 'BR', 'BS', 'BT', 'BU', 'BV', 'BW', 
        'BX', 'BY', 'BZ', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF',
        'CG', 'CH', 'CI', 'CJ', 'CK', 'CL', 'CM', 'CN', 'CO',
        'CP', 'CQ', 'CR', 'CS', 'CT', 'CU', 'CV', 'CW', 'CX',
        'CY', 'CZ'
    ]

    list_of_dataframes = []

    try:
        # Create a DataFrame for each subject and each day for that subject
        for i in range(len(name_list)): # iterate through subjects
            for j in range(int(day_list[i])): # Iterate through days for each subject
                df = pd.read_excel(excel_file, sheet_name=f"{name_list[i]}_r{j+1}", header=None)
                # Use as many labels as there are columns
                # .shape returns a tuple like (num_rows, num_cols); .shape[1] returns the exact num of cols in df
                num_cols = df.shape[1]
                if num_cols <= len(excel_columns):
                    df.columns = excel_columns[:num_cols] # slices excel_columns to only get as many col names as there are cols in df
                else:
                    # If we have more columns than labels, generate additional ones
                    extra_cols = [f"COL_{k}" for k in range(len(excel_columns), num_cols)]
                    df.columns = excel_columns + extra_cols
                df.at[2, 'A'] = f'{str(name_list[i])}_{str(j+1)}'
                df.at[0, 'A'] = np.nan
                list_of_dataframes.append(df)

        # Combine all the DataFrames together
        combined_df = pd.concat(list_of_dataframes, ignore_index=True)
        # print(combined_df)

        # Get the name of the subject for file naming
        # subject_name = df.iat[0, 0] # get a specific value at [row, column]

        file_name = f"group_{group}_sub_{subgroup}"
        os.makedirs(f"histograms_{date_time_string}/{file_name}", exist_ok=True) # create folder for subject if it doesn't exist
        file_path = os.path.abspath(f"histograms_{date_time_string}/{file_name}")

        # Iterate through speech data
        for i in range(31, 46):
            if i == 43:
                continue

            column_name = combined_df.iat[2, i]
            speech_data_1 = combined_df.iloc[:, i]

            # Flatten and convert to numeric, forcing errors to NaN, then drop NaNs
            speech_values_1 = pd.to_numeric(speech_data_1.values.flatten(), errors='coerce')
            speech_values_1 = speech_values_1[~np.isnan(speech_values_1)]

            # Plot speech level histogram
            plot_histogram(
                data1=speech_values_1,
                bins=np.arange(20, 95, 5),
                title=f"Distribution of Speech Levels ({column_name}): {group} ({subgroup}",
                xlabel="dB",
                file=f"histograms_{date_time_string}/{file_name}/{column_name}_speech_histogram.png",
            )

        # Iterate through SNR data
        for j in range(48, 63):
            if j == 60:
                continue

            column_name = combined_df.iat[2, j]
            snr_data_1 = combined_df.iloc[:, j]

            # Flatten and convert to numeric, forcing errors to NaN, then drop NaNs
            snr_values_1 = pd.to_numeric(snr_data_1.values.flatten(), errors='coerce')
            snr_values_1 = snr_values_1[~np.isnan(snr_values_1)]

            # Plot snr level histogram
            plot_histogram(
                data1=snr_values_1,
                bins=np.arange(-15, 35, 2.5),
                title=f"Distribution of SNR Levels ({column_name}): {group} ({subgroup})",
                xlabel="dB",
                file=f"histograms_{date_time_string}/{file_name}/{column_name}_snr_histogram.png",
            )

        # Clean DataFrame then convert into an Excel sheet for data replication
        combined_df = combined_df.drop(['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'], axis=1)
        combined_df.to_excel(f"{file_path}/combined_df_{file_name}.xlsx", index=False)
        print("Finished")
        print(f"Histograms saved at: {file_path}")
    except Exception as e:
        # If an error occurs, identify the error and find what line the error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        file_name = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        print(f"Error: {e}")
        print(f"File: {file_name}, Line: {line_number}")

def plot_histogram(data1, bins, title, xlabel, file):
    counts1, _ = np.histogram(data1, bins=bins) # an array of counts: each value represents how many values from data1 fall into each bin interval
    # print(counts1)

    total1 = counts1.sum()
    # print(total1)

    percentages1 = counts1 / total1 * 100

    bin_edges = bins[:-1]
    width = np.diff(bins)[0]

    # black bars for snr data, grey for speech data
    plt.figure(figsize=(8, 4))
    if "snr" in file:
         plt.bar(bin_edges - width/2, percentages1, width=width, color='black', alpha=0.7, edgecolor='black')
    else:
        plt.bar(bin_edges - width/2, percentages1, width=width, color='grey', alpha=0.7, edgecolor='black')

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel('%')
    plt.grid(False)
    plt.tight_layout()
    plt.savefig(file, dpi=300, bbox_inches='tight')
    plt.close()

def count_subject_recordings(subject, sheet_names):
    return sum(1 for name in sheet_names if name.startswith(subject + '_'))


def make_histogram_for_all(excel_file, name_list, day_list):

    excel_columns = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
        'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
        'U', 'V', 'W', 'X', 'Y', 'Z', 'AA', 'AB', 'AC', 'AD', 
        'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK', 'AL', 'AM', 
        'AN', 'AO', 'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AV', 
        'AW', 'AX', 'AY', 'AZ', 'BA', 'BB', 'BC', 'BD', 'BE', 
        'BF', 'BG', 'BH', 'BI', 'BJ', 'BK', 'BL', 'BM', 'BN', 
        'BO', 'BP', 'BQ', 'BR', 'BS', 'BT', 'BU', 'BV', 'BW', 
        'BX', 'BY', 'BZ', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF',
        'CG', 'CH', 'CI', 'CJ', 'CK', 'CL', 'CM', 'CN', 'CO',
        'CP', 'CQ', 'CR', 'CS', 'CT', 'CU', 'CV', 'CW', 'CX',
        'CY', 'CZ'
    ]

    list_of_dataframes = []

    # Create a DataFrame for each subject and each day for that subject
    for i in range(len(name_list)): # iterate through all 22 subjects
        for j in range(int(day_list[i])): # We're gonna assume that all subjects have 2 days of data
            df = pd.read_excel(excel_file, sheet_name=f"{name_list[i]}_r{j+1}", header=None)
            # Use as many labels as there are columns
            # .shape returns a tuple like (num_rows, num_cols); .shape[1] returns the exact num of cols in df
            num_cols = df.shape[1]
            if num_cols <= len(excel_columns):
                df.columns = excel_columns[:num_cols] # slices excel_columns to only get as many col names as there are cols in df
            else:
                # If we have more columns than labels, generate additional ones
                extra_cols = [f"COL_{k}" for k in range(len(excel_columns), num_cols)]
                df.columns = excel_columns + extra_cols
                
            df.at[2, 'A'] = f'{str(name_list[i])}_{str(j+1)}'
            df.at[0, 'A'] = np.nan
            list_of_dataframes.append(df)

    if list_of_dataframes:
        # Combine all the DataFrames together
        combined_df = pd.concat(list_of_dataframes, ignore_index=True)
        file_name = "all_subjects"
        os.makedirs(f"histograms_{date_time_string}/{file_name}", exist_ok=True)
        file_path = os.path.abspath(f"histograms_{date_time_string}/{file_name}")

        # Iterate through speech data
        for i in range(31, 46):
            if i == 43:
                continue

            column_name = combined_df.iat[2, i]
            speech_data_1 = combined_df.iloc[:, i]

            # Flatten and convert to numeric, forcing errors to NaN, then drop NaNs
            speech_values_1 = pd.to_numeric(speech_data_1.values.flatten(), errors='coerce')
            speech_values_1 = speech_values_1[~np.isnan(speech_values_1)]

            # Plot speech level histogram
            plot_histogram(
                data1=speech_values_1,
                bins=np.arange(20, 95, 5),
                title=f"Distribution of Speech Levels ({column_name}): All",
                xlabel="dB",
                file=f"histograms_{date_time_string}/{file_name}/{column_name}_speech_histogram.png",
            )

        # Iterate through SNR data
        for j in range(48, 63):
            if j == 60:
                continue

            column_name = combined_df.iat[2, j]
            snr_data_1 = combined_df.iloc[:, j]

            # Flatten and convert to numeric, forcing errors to NaN, then drop NaNs
            snr_values_1 = pd.to_numeric(snr_data_1.values.flatten(), errors='coerce')
            snr_values_1 = snr_values_1[~np.isnan(snr_values_1)]

            # Plot snr level histogram
            plot_histogram(
                data1=snr_values_1,
                bins=np.arange(-15, 35, 2.5),
                title=f"Distribution of SNR Levels ({column_name}): All",
                xlabel="dB",
                file=f"histograms_{date_time_string}/{file_name}/{column_name}_snr_histogram.png",
            )

        # Clean DataFrame then convert into an Excel sheet for data replication
        combined_df = combined_df.drop(['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'], axis=1)
        combined_df.to_excel(f"{file_path}/combined_df_{file_name}.xlsx", index=False)
        print(f"Histograms saved at: {file_path}")
    else:
        print("No data frames were successfully read.")



def make_histogram_for_each_participant(excel_file, name_list, day_list):
    excel_columns = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
        'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
        'U', 'V', 'W', 'X', 'Y', 'Z', 'AA', 'AB', 'AC', 'AD', 
        'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK', 'AL', 'AM', 
        'AN', 'AO', 'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AV', 
        'AW', 'AX', 'AY', 'AZ', 'BA', 'BB', 'BC', 'BD', 'BE', 
        'BF', 'BG', 'BH', 'BI', 'BJ', 'BK', 'BL', 'BM', 'BN', 
        'BO', 'BP', 'BQ', 'BR', 'BS', 'BT', 'BU', 'BV', 'BW', 
        'BX', 'BY', 'BZ', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF',
        'CG', 'CH', 'CI', 'CJ', 'CK', 'CL', 'CM', 'CN', 'CO',
        'CP', 'CQ', 'CR', 'CS', 'CT', 'CU', 'CV', 'CW', 'CX',
        'CY', 'CZ'
    ]

    # Create a DataFrame for each subject and each day for that subject
    for i in range(len(name_list)): # iterate through all 22 subjects
        list_of_dataframes_for_subject = []
        for j in range(int(day_list[i])): # We're gonna assume that all subjects have 2 days of data
            df = pd.read_excel(excel_file, sheet_name=f"{name_list[i]}_r{j+1}", header=None)
            # Use as many labels as there are columns
            # .shape returns a tuple like (num_rows, num_cols); .shape[1] returns the exact num of cols in df
            num_cols = df.shape[1]
            if num_cols <= len(excel_columns):
                df.columns = excel_columns[:num_cols] # slices excel_columns to only get as many col names as there are cols in df
            else:
                # If we have more columns than labels, generate additional ones
                extra_cols = [f"COL_{k}" for k in range(len(excel_columns), num_cols)]
                df.columns = excel_columns + extra_cols
            list_of_dataframes_for_subject.append(df)
        
        # Combine all days for this subject
        if list_of_dataframes_for_subject:
            combined_subject_df = pd.concat(list_of_dataframes_for_subject, ignore_index=True)
            
            file_name = name_list[i]
            os.makedirs(f"histograms_{date_time_string}/individual_participants/{file_name}", exist_ok=True)
            file_path = os.path.abspath(f"histograms_{date_time_string}/individual_participants/{file_name}")

            # Iterate through speech data
            for k in range(31, 46):
                if k == 43:
                    continue

                column_name = combined_subject_df.iat[2, k]
                speech_data_1 = combined_subject_df.iloc[:, k]

                # Flatten and convert to numeric, forcing errors to NaN, then drop NaNs
                speech_values_1 = pd.to_numeric(speech_data_1.values.flatten(), errors='coerce')
                speech_values_1 = speech_values_1[~np.isnan(speech_values_1)]

                # Plot speech level histogram
                plot_histogram(
                    data1=speech_values_1,
                    bins=np.arange(20, 95, 5),
                    title=f"Distribution of Speech Levels ({column_name}): {file_name}",
                    xlabel="dB",
                    file=f"histograms_{date_time_string}/individual_participants/{file_name}/{column_name}_speech_histogram.png",
                )

            # Iterate through SNR data
            for l in range(48, 63):
                if l == 60:
                    continue

                column_name = combined_subject_df.iat[2, l]
                snr_data_1 = combined_subject_df.iloc[:, l]

                # Flatten and convert to numeric, forcing errors to NaN, then drop NaNs
                snr_values_1 = pd.to_numeric(snr_data_1.values.flatten(), errors='coerce')
                snr_values_1 = snr_values_1[~np.isnan(snr_values_1)]

                # Plot snr level histogram
                plot_histogram(
                    data1=snr_values_1,
                    bins=np.arange(-15, 35, 2.5),
                    title=f"Distribution of SNR Levels ({column_name}): {file_name}",
                    xlabel="dB",
                    file=f"histograms_{date_time_string}/individual_participants/{file_name}/{column_name}_snr_histogram.png",
                )

            # Clean DataFrame then convert into an Excel sheet for data replication
            combined_subject_df = combined_subject_df.drop(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'], axis=1)
            combined_subject_df.to_excel(f"{file_path}/combined_df_{file_name}.xlsx", index=False)
            print(f"Histograms saved at: {file_path}")



def calculate_results(file_path):  # Add file_path parameter
    xls = pd.ExcelFile(file_path)

    # Get all sheet names
    sheet_names = xls.sheet_names

    # Extract unique participant identifiers from sheet names
    participants = set([name.split('_')[0] for name in sheet_names])
    # print(participants)

    # Define custom thresholds for specific participants and store them in a dictionary
    # threshold_df = pd.read_excel("subject_info_NIH.xlsx")
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    subject_info_path = os.path.join(script_dir, "subject_info_NIH.xlsx")
    threshold_df = pd.read_excel(subject_info_path)

    custom_thresholds = {
        row['Subject_Number']: row['Threshold_Score']
        # return each row as a tuple while ignoring the index and don't include scores that are NA 
        for _, row in threshold_df.iterrows()
        if pd.notnull(row['Threshold_Score']) and row['Threshold_Score'] != 'NA'
    }

    # Normalize keys to just the part before '_'
    custom_thresholds = {
        key.split('_')[0]: value
        for key, value in custom_thresholds.items()
    }

    # print(custom_thresholds.keys())

    # Function to accurately filter sheets for each participant
    def get_participant_sheets(participant):
        return [sheet for sheet in sheet_names if sheet.startswith(participant + '_')]

    # Define a function to process each sheet
    def process_sheet(sheet_name, participant):
        # Load the data from the specified sheet, using the third row as headers
        df = pd.read_excel(xls, sheet_name=sheet_name, header=2)

        # Select relevant columns and start from row 5 (index 4 in pandas)
        df_selected = df.iloc[4:, [48, 51]]

        # Rename columns for clarity
        df_selected.columns = ['Female', 'Male']

        # Convert columns to numeric, ignoring non-numeric values
        df_selected = df_selected.apply(pd.to_numeric, errors='coerce')

        # Count total values in each column
        total_female = df_selected['Female'].notna().sum()
        total_male = df_selected['Male'].notna().sum()
        total_combined = total_female + total_male

        # Define standard conditions
        conditions = {
            '>= 20': lambda x: x >= 20,
            '>= 15': lambda x: x >= 15,
            '>= 10': lambda x: x >= 10,
            '>= 5': lambda x: x >= 5,
            '>= 0': lambda x: x >= 0,
            '< 0': lambda x: x < 0,
            '<= -5': lambda x: x <= -5,
            '<= -10': lambda x: x <= -10,
        }

        # Add the participant-specific threshold dynamically
        if participant in custom_thresholds:
            # print(participant)
            # print(participant in custom_thresholds)
            threshold_value = custom_thresholds[participant]
            conditions[f'>= {threshold_value}'] = lambda x: x >= threshold_value

        # Count values based on specified ranges
        def count_values(column, condition):
            return (condition(column)).sum()

        # Calculate counts and percentages for each condition
        def calculate_counts_and_percentages(df, conditions, total_female, total_male, total_combined):
            results = []
            for label, condition in conditions.items():
                count_female = count_values(df['Female'], condition)
                count_male = count_values(df['Male'], condition)
                count_combined = count_female + count_male

                percentage_female = (count_female / total_female) * 100 if total_female else 0
                percentage_male = (count_male / total_male) * 100 if total_male else 0
                percentage_combined = (count_combined / total_combined) * 100 if total_combined else 0

                results.append({
                    'Range': label,
                    'Count_Female': count_female,
                    'Percentage_Female': percentage_female,
                    'Count_Male': count_male,
                    'Percentage_Male': percentage_male,
                    'Count_Combined': count_combined,
                    'Percentage_Combined': percentage_combined,
                })
            
            # Append the total counts to the results
            results.append({
                'Range': 'Total',
                'Count_Female': total_female,
                'Percentage_Female': np.nan,
                'Count_Male': total_male,
                'Percentage_Male': np.nan,
                'Count_Combined': total_combined,
                'Percentage_Combined': np.nan,
            })

            return results

        # Calculate counts and percentages for each condition
        results = calculate_counts_and_percentages(df_selected, conditions, total_female, total_male, total_combined)
        # print("results")

        # Convert results to DataFrame for display
        results_df = pd.DataFrame(results)
        # print(results_df)
        
        return results_df

    # Initialize list to hold all participants' results
    all_participants_results = []
    # Initialize list to hold summary data
    summary_data = []

    # Process each participant
    for participant in sorted(participants, key=lambda x: int(x[1:])):
        participant_sheets = get_participant_sheets(participant)
        participant_data = []

        for sheet in participant_sheets:
            sheet_data = process_sheet(sheet, participant)
            sheet_data['Sheet'] = sheet
            participant_data.append(sheet_data)
        
        # Combine data for all recording days for this participant
        participant_combined_data = pd.concat(participant_data, ignore_index=True)
        # print(participant_combined_data)
        
        # Calculate the standard average across days, excluding 'Total' row
        standard_average_results = participant_combined_data[participant_combined_data['Range'] != 'Total'].groupby('Range', observed=True).agg({
            'Count_Female': 'mean',
            'Percentage_Female': 'mean',
            'Count_Male': 'mean',
            'Percentage_Male': 'mean',
            'Count_Combined': 'mean',
            'Percentage_Combined': 'mean'
        }).reset_index()
        standard_average_results['Sheet'] = 'Average (Standard)'

        # Extract summary data, including custom threshold
        summary_row = {
            'Participant': participant,
        }

        # Add standard threshold summaries
        for threshold in ['>= 15', '>= 10', '>= 5', '>= 0']:
            summary_row[f'Standard_{threshold}'] = standard_average_results.loc[standard_average_results['Range'] == threshold, 'Percentage_Combined'].values[0]

        # Add custom threshold summary if available
        # print(participant)
        # print(participant in list(custom_thresholds.keys()))
        if participant in custom_thresholds:
            threshold_label = f'>= {custom_thresholds[participant]}'
            if threshold_label in standard_average_results['Range'].values:
                summary_row[f'Standard_{threshold_label}'] = standard_average_results.loc[standard_average_results['Range'] == threshold_label, 'Percentage_Combined'].values[0]

        summary_data.append(summary_row)

        # Append to all participants results
        all_participants_results.append(participant_combined_data)

    # Combine results for all participants
    final_combined_results = pd.concat(all_participants_results, ignore_index=True)

    # Define output file paths
    output_file_path = f'histograms_{date_time_string}/individual_analysis_results_combined_NIH_SAI_new.xlsx'
    summary_file_path = f'histograms_{date_time_string}/summary_results_NIH_SAI_new.xlsx'

    # Write the detailed DataFrame to an Excel file
    final_combined_results.to_excel(output_file_path, index=False)

    # Create and write the summary DataFrame to a separate Excel file
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(summary_file_path, index=False)

    print(f'Detailed results have been written to {output_file_path}')
    print(f'Summary results have been written to {summary_file_path}')


if __name__ == "__main__":
    # Add command line argument parsing
    print(sys.executable)
    parser = argparse.ArgumentParser(description='Create histograms from Excel data')
    parser.add_argument('file', help='Excel file path')
    parser.add_argument('--subject', '-s', type=str, 
                       help='Process specific subject(s). Examples: "S1", "S1,S5,S10", "S1-S5", "S1-S3,S10,S15-S17"')
    parser.add_argument('--each_day', action='store_true',
                        help='Create histograms and datasets for each day separately for the different groups and particpants analyzed')
    args = parser.parse_args()
    
    # Parse subject input into list
    target_subjects = parse_subject_range(args.subject) if args.subject else None
    
    if target_subjects:
        print(f"Target subjects specified: {', '.join(target_subjects)}")
    else:
        print("Processing all subjects")

    if ".xlsx" in args.file:
        if os.path.exists(args.file):

            file_to_read = args.file

            # subprocess.run(["python", "Code_Individual_Data_Percentages_SNRs._UPDATED_Each_Day.py", json.dumps(target_subjects), str(file_to_read)])

            # calculate_results()

            # Load subject info
            #subject_info_df = pd.read_excel("subject_info_NIH.xlsx")
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            subject_info_path = os.path.join(script_dir, "subject_info_NIH.xlsx")
            subject_info_df = pd.read_excel(subject_info_path)

            # Drop rows where Score or Subject_Name is NA
            subject_info_df = subject_info_df.dropna(subset=["Subject_Number"])

            # prevent duplicates by grouping clean, consistent values
            subject_info_df['Group'] = subject_info_df['Group'].str.strip()
            subject_info_df['Subgroup'] = subject_info_df['Subgroup'].astype(str).str.strip()

            # ('NH', 'NA') will appear instead of ('NH', nan), enabling to iterate over it like any other group
            subject_info_df['Subgroup'] = subject_info_df['Subgroup'].fillna('NA')

            # Filter subjects if target_subjects specified
            print(f'target_subjects {target_subjects}')
            print(subject_info_df)
            if target_subjects:
                filtered_subject_info, target_groups = filter_subjects_by_target(subject_info_df, target_subjects)
                if filtered_subject_info.empty:
                    exit(1)
            else:
                filtered_subject_info = subject_info_df
                target_groups = None

            # Load Excel file with recordings
            xls = pd.ExcelFile(args.file)  # Excel file provided via command line
            sheet_names = xls.sheet_names
            # print(sheet_names)

            # Get the current datetime object
            now = datetime.now()

            # Time format: Month Day, Year Hour:Minute AM/PM format
            date_time_string = now.strftime("%B %d, %Y %I:%M%p").replace(" ", "_")
            date_time_string = date_time_string.replace(":", "_")

            os.makedirs(f"histograms_{date_time_string}", exist_ok=True)

            # Group subjects by Group and Subgroup
            grouped = filtered_subject_info.groupby(["Group", "Subgroup"])
            # print(grouped.groups.keys())

            for (group, subgroup), group_df in grouped:
                # Skip this group if we have target subjects and this group isn't in target_groups
                if target_groups is not None and (group, subgroup) not in target_groups:
                    continue
                    
                # print(group_df)
                name_list = []
                day_list = []

                for _, row in group_df.iterrows():
                    subject = row['Subject_Number']
                    if subject in sheet_names or any(sheet.startswith(subject + "_") for sheet in sheet_names):
                        name_list.append(subject)
                        day_list.append(count_subject_recordings(subject, sheet_names))

                if name_list:
                    print(name_list)
                    print(f"Generating histograms for Group: {group}, Subgroup: {subgroup}")
                    make_histogram(file_to_read, name_list, day_list, group, subgroup)
                else:
                    print(f"Error: Unable to find participants in Group: {group}, Subgroup: {subgroup}")

            # Handle HA + CI combination only if relevant
            if target_groups is None or ('HL', 'HA + CI') in target_groups:
                # Filter for subgroup HA or CI (handle extra spaces just in case)
                ha_and_ci_df = filtered_subject_info[filtered_subject_info['Subgroup'].str.strip().isin(['HA', 'CI'])]

                combined_name_list = []
                combined_day_list = []

                for _, row in ha_and_ci_df.iterrows():
                    subject = row['Subject_Number']
                    if subject in sheet_names or any(sheet.startswith(subject + "_") for sheet in sheet_names):
                        combined_name_list.append(subject)
                        combined_day_list.append(count_subject_recordings(subject, sheet_names))

                if combined_name_list:
                    print("Generating histograms for CI and HA participants only")
                    make_histogram(file_to_read, combined_name_list, combined_day_list, group="HL", subgroup="HA + CI")
                else:
                     print("Error: Unable to find CI and HA participants.")

            # Handle individual participants - always update when processing any subjects
            if True:  # Always process individual participants
                all_name_list = []
                all_day_list = []

                # Loop through sheet names and extract subject IDs
                for sheet in sheet_names:
                    subject = re.sub(r"_r\d+$", "", sheet)
                    # Only include if this subject is in our filtered list (or if we're processing all)
                    if target_subjects is None or subject.split('_')[0] in target_subjects:
                        if subject in sheet_names or any(sheet.startswith(subject + "_") for sheet in sheet_names):
                            all_name_list.append(subject)
                            all_day_list.append(count_subject_recordings(subject, sheet_names))

                if all_name_list:
                    print("Generating histograms for all participants")
                    make_histogram_for_all(file_to_read, all_name_list, all_day_list)

            # Handle all subjects - always update when processing any subjects  
            if True:  # Always process all subjects data    
                individual_name_list = []
                individual_day_list = []

                # Loop through sheet names and extract subject IDs
                for sheet in sheet_names:
                    subject = re.sub(r"_r\d+$", "", sheet)
                    # Only include if this subject is in our filtered list (or if we're processing all)
                    if target_subjects is None or subject.split('_')[0] in target_subjects:
                        if subject in sheet_names or any(sheet.startswith(subject + "_") for sheet in sheet_names):
                            individual_name_list.append(subject)
                            individual_day_list.append(count_subject_recordings(subject, sheet_names))

                if individual_name_list:
                    print("Generating histograms for each participant")
                    make_histogram_for_each_participant(file_to_read, individual_name_list, individual_day_list)

            # Calculate summary results and individual analysis
            calculate_results(file_to_read)

            # Plot histograms for each day only but run as a separate script
            if args.each_day:
                print("Making histograms for each individual day as a separate script: ")
                subprocess.run(["python", "FinalPythonScripts/Code_Individual_Data_Percentages_SNRs._UPDATED_Each_Day.py", json.dumps(target_subjects), str(file_to_read)])

        else:
            print(f"Error: Could not find file '{args.file}'.\nPlease make sure provided file exists in the same directory as this script.")
    else:
        print("Error: Invalid file type provided. Please make sure you're reading from an .xlsx (excel) file")