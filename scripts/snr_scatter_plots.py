import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import argparse
import os
from pathlib import Path
import re
from datetime import datetime, time
import plotly.io as pio
from typing import List



def extract_subject_number(sheet_name):
    """Extract subject number from sheet name (e.g., 'S07_r1' -> 'S07')"""
    match = re.match(r'(S\d+)', sheet_name)
    return match.group(1) if match else None

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


def parse_time_column(time_series):
    """Convert time strings to datetime objects for proper plotting"""
    parsed_times = []
    for time_str in time_series:
        if pd.isna(time_str) or time_str == '':
            parsed_times.append(None)
        else:
            try:
                # Parse time in HH:MM:SS format
                if isinstance(time_str, str):
                    time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
                else:
                    # Handle if it's already a time object
                    time_obj = time_str
                parsed_times.append(time_obj)
            except:
                parsed_times.append(None)
    return parsed_times

def create_interactive_scatter_plot(x_data, y_data, x_label, y_label, title, save_path, show_data=True):
    """Create an interactive scatter plot with fixed time axis from 6AM to 22:00"""
    # Remove NaN values
    df_plot = pd.DataFrame({'x': x_data, 'y': y_data})
    df_plot = df_plot.dropna()
    
    if len(df_plot) == 0:
        print(f"No valid data for {title}")
        return
    
    # Convert time strings to datetime objects for proper plotting
    df_plot['time_obj'] = pd.to_datetime(df_plot['x'], format='%H:%M:%S', errors='coerce')
    df_plot = df_plot.dropna(subset=['time_obj'])
    df_plot = df_plot.sort_values('time_obj')
    
    # Convert to hours since midnight for continuous plotting
    df_plot['hours_since_midnight'] = df_plot['time_obj'].dt.hour + df_plot['time_obj'].dt.minute/60 + df_plot['time_obj'].dt.second/3600
    
    # Show the actual data being plotted
    if show_data:
        print(f"\n    === DATA USED FOR {title} ===")
        print(f"    Total data points: {len(df_plot)}")
        if len(df_plot) > 0:
            print(f"    Time range: {df_plot['x'].iloc[0]} to {df_plot['x'].iloc[-1]}")
            print(f"    Y-value range: {df_plot['y'].min():.2f} to {df_plot['y'].max():.2f}")
        
        # Save data to CSV for reference
        csv_path = save_path.with_suffix('.csv')
        df_plot[['x', 'y']].to_csv(csv_path, index=False)
        print(f"    Data saved to: {csv_path}")
        print(f"    ===============================\n")
    
    # Create the interactive plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_plot['hours_since_midnight'],
        y=df_plot['y'],
        mode='markers',  # CHANGED: Connect points with lines -> changed back
        marker=dict(
            size=6,
            color='steelblue',
            opacity=0.7
        ),
        name='Data Points',
        text=df_plot['x'],  # Original time strings for hover
        hovertemplate='<b>Time:</b> %{text}<br><b>' + y_label + ':</b> %{y:.2f}<extra></extra>'
    ))
    
    # Set fixed time axis from 6AM to 22:00 (10PM)
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=16, family="Arial Black")
        ),
        xaxis=dict(
            title=x_label,
            showgrid=True,
            gridcolor='lightgray',
            type='linear',
            range=[6, 22],  # 6AM to 10PM
            tickmode='array',
            tickvals=list(range(6, 23)),
            ticktext=[f"{hour:02d}:00" for hour in range(6, 23)],
            dtick=1
        ),
        yaxis=dict(
            title=y_label,
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        hovermode='closest',
        width=1200,
        height=600
    )
    
    # Save as interactive HTML
    html_path = save_path.with_suffix('.html')
    fig.write_html(html_path)
    
    # Also save as static PNG for backup
    png_path = save_path.with_suffix('.png')
    fig.write_image(png_path, width=1200, height=600, scale=2)
    
    print(f"    Saved interactive plot: {html_path}")
    print(f"    Saved static plot: {png_path}")
def process_excel_file(file_path, target_subjects=None):
    """Main function to process the Excel file and create scatter plots"""
    
    # Set default renderer for better compatibility
    pio.renderers.default = "browser"
    
    # Define all columns to plot
    basic_columns = [
        'OLN(c)(dB)', 'OLF(c) (dB)', 'OLN(p) (dB)', 'OLF(p) (dB)', 'Weighted Noise (dB)'
    ]
    
    speech_snr_columns = [
        'Female', 'FAN', 'FAF', 'Male', 'MAN', 'MAF', 'Other Ch', 'CXN', 'CXF', 
        'Comb-All', 'Combined-N', 'Combined-F', 'CHN', 'CHF'
    ]
    
    # Read all sheet names
    xl_file = pd.ExcelFile(file_path)
    sheet_names = xl_file.sheet_names
    
    # Group sheets by subject
    subjects = {}
    for sheet in sheet_names:
        subject = extract_subject_number(sheet)
        if subject:
            if subject not in subjects:
                subjects[subject] = []
            subjects[subject].append(sheet)

    # Filter to specific subjects if requested
    if target_subjects:
        # Filter subjects dictionary to only include target subjects
        filtered_subjects = {subj: subjects[subj] for subj in target_subjects if subj in subjects}
        
        if filtered_subjects:
            subjects = filtered_subjects
            print(f"Processing subjects: {list(subjects.keys())}")
            
            # Warn about any subjects that weren't found
            missing_subjects = [subj for subj in target_subjects if subj not in subjects]
            if missing_subjects:
                print(f"Warning: Subjects not found in data: {missing_subjects}")
                print(f"Available subjects: {list(subjects.keys())}")
        else:
            print(f"None of the specified subjects found in data: {target_subjects}")
            print(f"Available subjects: {list(subjects.keys())}")
            return
    else:
        print(f"Processing all subjects: {list(subjects.keys())}")

    
    # Create base directory for plots
    script_dir = Path(file_path).parent.parent.parent
    base_dir = script_dir / 'outputs' / 'SNR_Interactive_Plots'
    base_dir.mkdir(exist_ok=True)
    
    # Process each subject
    for subject, sheets in subjects.items():
        print(f"Processing subject {subject}...")
        
        # Create subject directory
        subject_dir = base_dir / subject
        subject_dir.mkdir(exist_ok=True)

        # Create subfolders for different plot types
        basic_plots_dir = subject_dir / 'basic_measurements'
        weighted_speech_dir = subject_dir / 'weighted_speech'
        snr_plots_dir = subject_dir / 'snr_plots'
        
        basic_plots_dir.mkdir(exist_ok=True)
        weighted_speech_dir.mkdir(exist_ok=True)
        snr_plots_dir.mkdir(exist_ok=True)
        
        # Process each day separately
        for day_num, sheet in enumerate(sheets, 1):
            print(f"\n  === PROCESSING DAY {day_num} (Sheet: {sheet}) ===")
            
            try:
                # Read the sheet without any assumptions about structure
                df_raw = pd.read_excel(file_path, sheet_name=sheet, header=None)
                
                print(f"    Sheet dimensions: {df_raw.shape}")
                
                # Look for header row containing key column names
                header_row = None
                key_headers = ['conversation number', 'conv. start', 'startclock', 'weighted noise']
                
                for i, row in df_raw.iterrows():
                    row_str = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
                    if any(header.lower() in row_str for header in key_headers):
                        header_row = i
                        print(f"    Found header row at index: {i}")
                        break
                
                if header_row is None:
                    print(f"    Could not find header row in sheet {sheet}")
                    continue
                
                # Read with the found header row
                day_data = pd.read_excel(file_path, sheet_name=sheet, skiprows=header_row)
                
                # Clean up column names
                day_data.columns = day_data.columns.astype(str)
                
                print(f"    Columns after reading: {list(day_data.columns[:10])}...")
                print(f"    Full data shape: {day_data.shape}")
                
                # Based on your Excel structure, data starts after the "Weighted Mean" row
                data_start_row = None
                for idx, row in day_data.iterrows():
                    row_str = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
                    if 'weighted mean' in row_str:
                        data_start_row = idx + 1
                        print(f"    Found 'Weighted Mean' at row {idx}, data starts at row {data_start_row}")
                        break
                
                if data_start_row is None:
                    data_start_row = 2
                    print(f"    Could not find 'Weighted Mean' row, assuming data starts at row {data_start_row}")
                
                # Filter to only the actual conversation data rows
                conversation_data = day_data.iloc[data_start_row:].copy()
                conversation_data = conversation_data.dropna(how='all')
                
                print(f"    Extracted {len(conversation_data)} conversation data rows")
                print(f"    Available columns: {list(conversation_data.columns)}")
                
                # Find time column (StartClock)
                start_clock_col = None
                for col in conversation_data.columns:
                    col_lower = str(col).lower().strip()
                    if 'startclock' in col_lower or 'start clock' in col_lower:
                        start_clock_col = col
                        print(f"    Found time column: '{col}'")
                        break
                
                if start_clock_col is None:
                    print(f"    StartClock column not found for day {day_num}")
                    print(f"    Available columns: {list(conversation_data.columns)}")
                    continue
                
                # Parse time data
                time_data = []
                for time_val in conversation_data[start_clock_col]:
                    if pd.notna(time_val):
                        time_data.append(str(time_val))
                    else:
                        time_data.append(None)
                
                print(f"    Processed {len([t for t in time_data if t is not None])} time points")
                
                # Define exact column names based on your Excel structure
                basic_columns_exact = [
                    'OLN(c)(dB)', 'OLF(c) (dB)', 'OLN(p) (dB)', 'OLF(p) (dB)', 'Weighted Noise (dB)'
                ]
                
                speech_snr_columns_exact = [
                    'Female', 'FAN', 'FAF', 'Male', 'MAN', 'MAF', 'Other Ch', 'CXN', 'CXF', 
                    'Comb-All', 'Combined-N', 'Combined-F', 'CHN', 'CHF'
                ]
                
                # Create plots for basic columns
                print(f"    Creating plots for basic columns...")
                for col_name in basic_columns_exact:
                    col_found = None
                    for col in conversation_data.columns:
                        if str(col).strip() == col_name:
                            col_found = col
                            break
                    
                    if col_found:
                        print(f"      Found column: {col_name}")
                        safe_name = col_name.replace('(', '').replace(')', '').replace(' ', '_')
                        save_path = basic_plots_dir / f"{subject}_Day{day_num}_{safe_name}"
                        create_interactive_scatter_plot(
                            time_data,
                            conversation_data[col_found],
                            'Time of Day',
                            col_name,
                            f'{subject} Day {day_num} - {col_name} vs Time',
                            save_path
                        )
                    else:
                        print(f"      Column not found: {col_name}")
                
                # Find the start of Weighted Speech section
                weighted_speech_start = None
                snr_start = None
                
                # Create plots for Weighted Speech columns
                if weighted_speech_start is None:
                    # Manually find the weighted speech start by looking for 'Female' column
                    for i, col in enumerate(conversation_data.columns):
                        if str(col).strip() == 'Female':
                            weighted_speech_start = i
                            print(f"    Found Weighted Speech section by 'Female' column at position {i}")
                            break

                if snr_start is None:
                    # Manually find the SNR start by looking for 'Female.1' column  
                    for i, col in enumerate(conversation_data.columns):
                        if str(col).strip() == 'Female.1':
                            snr_start = i
                            print(f"    Found SNR section by 'Female.1' column at position {i}")
                            break

                # Create plots for Weighted Speech columns
                if weighted_speech_start is not None:
                    print(f"    Creating plots for Weighted Speech columns...")
                    for i, col_name in enumerate(speech_snr_columns_exact):
                        col_index = weighted_speech_start + i
                        if col_index < len(conversation_data.columns):
                            actual_col = conversation_data.columns[col_index]
                            if str(actual_col).strip().lower() != 'nan':
                                print(f"      Processing Weighted Speech: {col_name} -> {actual_col}")
                                safe_name = col_name.replace(' ', '_').replace('-', '_')
                                save_path = weighted_speech_dir / f"{subject}_Day{day_num}_Weighted_Speech_{safe_name}"
                                create_interactive_scatter_plot(
                                    time_data,
                                    conversation_data[actual_col],
                                    'Time of Day',
                                    f'Weighted Speech {col_name} (dB)',
                                    f'{subject} Day {day_num} - Weighted Speech {col_name} vs Time',
                                    save_path
                                )
                
                # Create plots for SNR columns
                if snr_start is not None:
                    print(f"    Creating plots for SNR columns...")
                    for i, col_name in enumerate(speech_snr_columns_exact):
                        col_index = snr_start + i
                        if col_index < len(conversation_data.columns):
                            actual_col = conversation_data.columns[col_index]
                            if str(actual_col).strip().lower() != 'nan':
                                print(f"      Processing SNR: {col_name} -> {actual_col}")
                                safe_name = col_name.replace(' ', '_').replace('-', '_')
                                save_path = snr_plots_dir / f"{subject}_Day{day_num}_SNR_{safe_name}"
                                create_interactive_scatter_plot(
                                    time_data,
                                    conversation_data[actual_col],
                                    'Time of Day',
                                    f'SNR {col_name} (dB)',
                                    f'{subject} Day {day_num} - SNR {col_name} vs Time',
                                    save_path
                                )
                    # Create additional combined SNR plots
                    print(f"    Creating additional combined SNR plots...")
                    
                    # Find the specific columns we need
                    female_snr_col = None
                    male_snr_col = None
                    other_ch_snr_col = None
                    
                    for i, col in enumerate(conversation_data.columns):
                        if str(col).strip() == 'Female.1':
                            female_snr_col = col
                        elif str(col).strip() == 'Male.1':
                            male_snr_col = col
                        elif str(col).strip() == 'Other Ch.1':
                            other_ch_snr_col = col
                    
                    # Plot 1: Male + Female SNR
                    if female_snr_col and male_snr_col:
                        print(f"      Creating Male + Female SNR plot...")
                        combined_male_female = pd.to_numeric(conversation_data[male_snr_col], errors='coerce') + pd.to_numeric(conversation_data[female_snr_col], errors='coerce')
                        save_path = snr_plots_dir / f"{subject}_Day{day_num}_SNR_Male_Plus_Female_Combined"
                        create_interactive_scatter_plot(
                            time_data,
                            combined_male_female,
                            'Time of Day',
                            'SNR Male + Female Combined (dB)',
                            f'{subject} Day {day_num} - SNR Male + Female Combined vs Time',
                            save_path
                        )
                    
                    # Plot 2: Female + Male + Other Ch SNR
                    if female_snr_col and male_snr_col and other_ch_snr_col:
                        print(f"      Creating Female + Male + Other Ch SNR plot...")
                        combined_all_three = (pd.to_numeric(conversation_data[female_snr_col], errors='coerce') + 
                                            pd.to_numeric(conversation_data[male_snr_col], errors='coerce') + 
                                            pd.to_numeric(conversation_data[other_ch_snr_col], errors='coerce'))
                        save_path = snr_plots_dir / f"{subject}_Day{day_num}_SNR_Female_Male_OtherCh_Combined"
                        create_interactive_scatter_plot(
                            time_data,
                            combined_all_three,
                            'Time of Day',
                            'SNR Female + Male + Other Ch Combined (dB)',
                            f'{subject} Day {day_num} - SNR Female + Male + Other Ch Combined vs Time',
                            save_path
                        )
                
                print(f"    ================================")
                
            except Exception as e:
                print(f"    Error processing day {day_num} (sheet {sheet}): {e}")
                continue
    print("\nAll scatter plots generated!")
    print(f"Plots saved in: {base_dir}")


# Usage
if __name__ == "__main__":
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description='Create SNR scatter plots from Excel data')
    parser.add_argument('--subjects', '-s', type=str, 
                       help='Process specific subject(s). Examples: "S1", "S1,S5,S10", "S1-S5", "S1-S3,S10,S15-S17"')
    args = parser.parse_args()
    
    # Parse subject input into list
    target_subjects = parse_subject_range(args.subjects) if args.subjects else None
    
    # File path relative to the script location
    script_dir = Path(__file__).parent
    excel_file_path = script_dir / "FinalPythonScripts" / "Individual_SNR_Power_NIH.xlsx"
 
    if target_subjects:
        print(f"Processing subjects: {', '.join(target_subjects)}")
    else:
        print("Processing all subjects")
    
    if excel_file_path.exists():
        process_excel_file(excel_file_path, target_subjects=target_subjects)
    else:
        print(f"Excel file not found: {excel_file_path}")