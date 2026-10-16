#!/usr/bin/env python3
"""
smoothed_snr_plots_no_ema.py - Create smoothed SNR plots without activity data

*** NO-EMA VERSION ***
This modified version creates smoothed plots showing only SNR/dB measurements.
No activity timeline overlays are included.

This script creates smoothed SNR and dB measurement plots over time
without overlaying activity timeline data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from datetime import datetime, time
import argparse
import re
import warnings
warnings.filterwarnings('ignore')



def save_plot_data_to_csv(measurement_data_list, subject, day, save_path, window_minutes=15):
    """Save the plot data to CSV files for reproducibility (no activity data)"""
    
    # Prepare the base CSV data dictionary
    csv_data = {}
    
    # Process smoothed measurement data (EXACT SAME as overlay script)
    if measurement_data_list:
        # Get all unique time points from all measurements
        all_times = set()
        measurement_dict = {}
        
        for measurement_item in measurement_data_list:
            # Handle both 2-tuple and 3-tuple formats
            if len(measurement_item) == 2:
                measurement_data, measurement_name = measurement_item
            elif len(measurement_item) == 3:
                measurement_data, measurement_name, _ = measurement_item
            else:
                continue
            
            if measurement_data is not None and len(measurement_data) > 0:
                # Determine the correct column names
                time_col = 'time_hours' if 'time_hours' in measurement_data.columns else 'Elapsed_Time'
                
                # Find the value column - try multiple options
                value_col = None
                if 'y' in measurement_data.columns:
                    value_col = 'y'
                elif measurement_name in measurement_data.columns:
                    value_col = measurement_name
                elif 'SNR' in measurement_data.columns:
                    value_col = 'SNR'
                else:
                    # Try to find any numeric column
                    numeric_cols = measurement_data.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        value_col = numeric_cols[0]
                
                if time_col in measurement_data.columns and value_col is not None:
                    # Apply smoothing to this measurement
                    smoothed_data = smooth_data_moving_average(measurement_data, time_col, value_col, window_minutes)
                    
                    if len(smoothed_data) > 0:
                        times = smoothed_data[time_col].tolist()
                        values = smoothed_data[value_col].tolist()
                        
                        all_times.update(times)
                        measurement_dict[measurement_name] = dict(zip(times, values))
        
        # Create sorted time array
        sorted_times = sorted(list(all_times))
        csv_data['Time_Hours'] = sorted_times
        
        # Add measurement columns
        for measurement_name, time_value_dict in measurement_dict.items():
            # Create safe column name
            safe_name = measurement_name.replace(' ', '_').replace('/', '_').replace('-', '_')
            measurement_values = []
            
            for time_point in sorted_times:
                if time_point in time_value_dict:
                    measurement_values.append(time_value_dict[time_point])
                else:
                    measurement_values.append(None)  # Use None for missing values
            
            csv_data[f'SNR_{safe_name}'] = measurement_values
    
    # Save to CSV if we have data
    if csv_data:
        df_combined = pd.DataFrame(csv_data)
        csv_path = save_path.with_suffix('.csv')
        df_combined.to_csv(csv_path, index=False)
        print(f"        Saved plot data to CSV: {csv_path}")
        return csv_path
    
    return None

def parse_subject_range(subject_input):
    """Parse subject input supporting ranges and mixed selections"""
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


def parse_time_string(time_str):
    """Convert time string to hours since midnight"""
    try:
        if pd.isna(time_str):
            return None
        # Try parsing as time
        time_obj = datetime.strptime(str(time_str), '%H:%M:%S').time()
        return time_obj.hour + time_obj.minute/60 + time_obj.second/3600
    except:
        try:
            # Try without seconds
            time_obj = datetime.strptime(str(time_str), '%H:%M').time()
            return time_obj.hour + time_obj.minute/60
        except:
            return None


def load_snr_data(snr_csv_path):
    """Load and process SNR data from CSV"""
    try:
        df = pd.read_csv(snr_csv_path)
        
        # Parse time column
        if 'x' in df.columns:
            df['time_hours'] = df['x'].apply(parse_time_string)
            df = df.dropna(subset=['time_hours'])
            
            # Get the measurement name from filename
            filename = Path(snr_csv_path).stem
            print(f"        Processing file: {filename}")
            
            # Determine measurement type and name 
            is_basic_measurement = False
            
            if 'Weighted_Noise' in filename or 'Weighted' in filename:
                measurement_name = "Weighted Noise (dB)"
                is_basic_measurement = True
            elif 'OLF_c' in filename or 'OLFc' in filename:
                measurement_name = "OLF(c) (dB)"
                is_basic_measurement = True
            elif 'OLF_p' in filename or 'OLFp' in filename:
                measurement_name = "OLF(p) (dB)"
                is_basic_measurement = True
            elif 'OLN_c' in filename or 'OLNc' in filename:
                measurement_name = "OLN(c) (dB)"
                is_basic_measurement = True
            elif 'OLN_p' in filename or 'OLNp' in filename:
                measurement_name = "OLN(p) (dB)"
                is_basic_measurement = True
            elif 'SNR_Female_Male_OtherCh_Combined' in filename:
                measurement_name = "SNR Combined (Female+Male+Other Ch)"
            elif 'SNR_Male_Plus_Female_Combined' in filename:
                measurement_name = "SNR Combined (Female+Male)"
            elif 'SNR_Female' in filename:
                measurement_name = "SNR Female"
            elif 'SNR_Male' in filename:
                measurement_name = "SNR Male"
            elif 'SNR_Comb_All' in filename:
                measurement_name = "SNR Combined All"
            elif 'SNR_CXN' in filename:
                measurement_name = "SNR CXN"
            elif 'SNR_CXF' in filename:
                measurement_name = "SNR CXF"
            elif 'SNR_FAN' in filename:
                measurement_name = "SNR FAN"
            elif 'SNR_FAF' in filename:
                measurement_name = "SNR FAF"
            elif 'SNR_MAN' in filename:
                measurement_name = "SNR MAN"
            elif 'SNR_MAF' in filename:
                measurement_name = "SNR MAF"
            elif 'SNR_CHN' in filename:
                measurement_name = "SNR CHN"
            elif 'SNR_CHF' in filename:
                measurement_name = "SNR CHF"
            elif 'SNR_Other_Ch' in filename:
                measurement_name = "SNR Other Ch"
            elif 'SNR_Combined_F' in filename:
                measurement_name = "SNR Combined F"
            elif 'SNR_Combined_N' in filename:
                measurement_name = "SNR Combined N"
            else:
                # Fallback parsing
                filename_lower = filename.lower()
                if any(x in filename_lower for x in ['olf', 'oln', 'weighted', 'noise']):
                    is_basic_measurement = True
                    if 'weighted' in filename_lower and 'noise' in filename_lower:
                        measurement_name = "Weighted Noise (dB)"
                    else:
                        measurement_name = f"Unknown dB Measurement"
                else:
                    measurement_name = filename.replace('_', ' ')
            
            return df, measurement_name, is_basic_measurement
        else:
            print(f"        Warning: No 'x' column found in {filename}")
            return None, None, None
            
    except Exception as e:
        print(f"        Error loading {snr_csv_path}: {e}")
        return None, None, None

def apply_smoothing(df, time_col='time_hours', value_col='y', window_minutes=15):
    """Apply moving average smoothing to measurement data"""
    if df is None or len(df) == 0:
        return pd.DataFrame()
    
    # Convert window to hours
    window_hours = window_minutes / 60
    
    # Sort by time
    df = df.sort_values(time_col).copy()
    
    # Apply rolling mean
    smoothed_values = []
    smoothed_times = []
    
    # Create time windows
    for i in range(len(df)):
        current_time = df.iloc[i][time_col]
        
        # Find points within window
        window_mask = (df[time_col] >= current_time - window_hours/2) & \
                     (df[time_col] <= current_time + window_hours/2)
        window_data = df[window_mask]
        
        if len(window_data) > 0:
            smoothed_values.append(window_data[value_col].mean())
            smoothed_times.append(current_time)
    
    return pd.DataFrame({
        time_col: smoothed_times,
        value_col: smoothed_values
    })

def smooth_data_moving_average(df, time_col, value_col, window_minutes=15):
    """Apply moving average smoothing to time series data"""
    if len(df) < 2:
        return df
    
    # Sort by time
    df_sorted = df.sort_values(time_col).copy()
    
    # Convert window from minutes to hours
    window_hours = window_minutes / 60
    
    smoothed_values = []
    smoothed_times = []
    
    for i, row in df_sorted.iterrows():
        current_time = row[time_col]
        
        # Define time window around current point
        time_min = current_time - window_hours/2
        time_max = current_time + window_hours/2
        
        # Get data points within window
        window_data = df_sorted[
            (df_sorted[time_col] >= time_min) & 
            (df_sorted[time_col] <= time_max)
        ]
        
        if len(window_data) > 0:
            smoothed_values.append(window_data[value_col].mean())
            smoothed_times.append(current_time)
    
    return pd.DataFrame({
        time_col: smoothed_times,
        value_col: smoothed_values
    })



def create_smoothed_plot(measurement_data_list, subject, day, save_path, plot_type="SNR", window_minutes=15):
    """Create plot with smoothed measurement lines (no activity overlay) - matches overlay script structure"""

    # Save plot data to CSV first (no activity data)
    csv_path = save_plot_data_to_csv(measurement_data_list, subject, day, save_path, window_minutes)
    
    # Create subplot with secondary y-axis (same as overlay script)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Set plot titles based on type (match overlay script titles)
    if plot_type == "dB_measurements":
        main_title = f'{subject} Day {day} - Smoothed dB Measurements'
        y_axis_title = "dB Measurements"
    else:
        main_title = f'{subject} Day {day} - Smoothed SNR Measurements'
        y_axis_title = "SNR Measurements (dB)"
    
    # Add smoothed measurement lines on primary y-axis
    colors = ['blue', 'red', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan', 'magenta']
    
    # Track processed measurements to avoid duplicates
    processed_measurements = set()
    
    if measurement_data_list:
        for i, measurement_item in enumerate(measurement_data_list):
            # Handle both 2-tuple and 3-tuple formats
            if len(measurement_item) == 2:
                measurement_data, measurement_name = measurement_item
                is_basic_measurement = False  # default value
            elif len(measurement_item) == 3:
                measurement_data, measurement_name, is_basic_measurement = measurement_item
            else:
                continue
            
            if measurement_data is not None and len(measurement_data) > 0:
                # Skip duplicate measurements
                if measurement_name in processed_measurements:
                    print(f"        Skipping duplicate measurement: {measurement_name}")
                    continue
                
                processed_measurements.add(measurement_name)
                
                # Apply smoothing
                time_col = 'time_hours' if 'time_hours' in measurement_data.columns else 'Elapsed_Time'
                value_col = 'y' if 'y' in measurement_data.columns else 'SNR'
                smoothed_data = smooth_data_moving_average(measurement_data, time_col, value_col, window_minutes)
                
                if len(smoothed_data) > 0:
                    color = colors[i % len(colors)]
                    
                    fig.add_trace(
                        go.Scatter(
                            x=smoothed_data[time_col],
                            y=smoothed_data[value_col],
                            mode='lines',
                            name=f'{measurement_name} (smoothed)',
                            line=dict(color=color, width=2),
                            hovertemplate=f'<b>{measurement_name}</b><br>' +
                                         f'Time: %{{x:.2f}} hours<br>' +
                                         f'{y_axis_title}: %{{y:.2f}}<br>' +
                                         f'Smoothed over {window_minutes} min<extra></extra>'
                            # REMOVED: legendgroup="measurements" - this was grouping them together
                            # Each measurement now has its own individual legend entry
                        ),
                        secondary_y=False
                    )
    
    # Update layout (EXACT SAME as overlay script)
    fig.update_layout(
        title=dict(
            text=main_title,
            x=0.5,
            font=dict(size=16, family="Arial Black")
        ),
        xaxis=dict(
            title='Time of Day (hours since midnight)',
            showgrid=True,
            gridcolor='lightgray',
            range=[6, 22],  # 6AM to 10PM
            tickmode='array',
            tickvals=list(range(6, 23)),
            ticktext=[f"{hour:02d}:00" for hour in range(6, 23)]
        ),
        plot_bgcolor='white',
        hovermode='x unified',
        width=1600,
        height=800,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    
    # Update y-axes (EXACT SAME as overlay script)
    fig.update_yaxes(
        title_text=y_axis_title,
        showgrid=True,
        gridcolor='lightgray',
        secondary_y=False
    )
    
    fig.update_yaxes(
        title_text="Activities",
        showgrid=False,
        secondary_y=True
    )
    
    return fig

def find_snr_files(snr_dir, subject, day):
    """Find all SNR CSV files for a subject and day"""
    snr_files = []
    
    # Look for files in basic_measurements subdirectory
    basic_dir = snr_dir / subject / 'basic_measurements'
    if basic_dir.exists():
        for csv_file in basic_dir.glob(f"{subject}_Day{day}_*.csv"):
            snr_files.append(csv_file)
        for csv_file in basic_dir.glob(f"{subject}_day{day}_*.csv"):
            snr_files.append(csv_file)
    
    # Look for files in snr_plots subdirectory
    snr_plots_dir = snr_dir / subject / 'snr_plots'
    if snr_plots_dir.exists():
        for csv_file in snr_plots_dir.glob(f"{subject}_Day{day}_*.csv"):
            snr_files.append(csv_file)
        for csv_file in snr_plots_dir.glob(f"{subject}_day{day}_*.csv"):
            snr_files.append(csv_file)
    
    # Look for files in weighted_speech subdirectory
    weighted_dir = snr_dir / subject / 'weighted_speech'
    if weighted_dir.exists():
        for csv_file in weighted_dir.glob(f"{subject}_Day{day}_*.csv"):
            snr_files.append(csv_file)
        for csv_file in weighted_dir.glob(f"{subject}_day{day}_*.csv"):
            snr_files.append(csv_file)
    
    return snr_files

def process_smoothed_plots(base_dir, subjects=None, days=None, window_minutes=15):
    """Main function to create smoothed SNR plots"""
    
    print(f"\nCreating smoothed SNR plots (no activities)...")
    print(f"Smoothing window: {window_minutes} minutes")
    
    # Define paths
    snr_dir = base_dir / "SNR_Interactive_Plots"
    output_base_dir = base_dir / "Smoothed_SNR_Plots_No_Activities"
    
    # Check if SNR directory exists
    if not snr_dir.exists():
        print(f"Error: SNR plots directory not found: {snr_dir}")
        return
    
    # Create output directory
    output_base_dir.mkdir(exist_ok=True)
    
    # Get all available subjects if not specified
    if not subjects:
        # Find all subject directories
        subject_dirs = [d for d in snr_dir.iterdir() if d.is_dir() and d.name.startswith('S')]
        subjects = sorted([d.name for d in subject_dirs])
    
    print(f"Processing subjects: {', '.join(subjects)}")
    
    # Process each subject
    for subject in subjects:
        print(f"\n  Processing {subject}...")
        
        # Create subject output directory
        subject_output_dir = output_base_dir / subject
        subject_output_dir.mkdir(exist_ok=True)
        
        # Find available days for this subject by looking in subdirectories
        available_days = set()
        subject_dir = snr_dir / subject

        # Look in all subdirectories for day files
        for subdir in ['basic_measurements', 'snr_plots', 'weighted_speech']:
            subdir_path = subject_dir / subdir
            if subdir_path.exists():
                subject_files = list(subdir_path.glob(f"{subject}_Day*.csv"))
                for f in subject_files:
                    day_match = re.search(r'Day(\d+)', f.name)
                    if day_match:
                        available_days.add(int(day_match.group(1)))

        available_days = sorted(list(available_days))
        
        if days:
            # Filter to requested days
            available_days = [d for d in available_days if str(d) in days]
        
        print(f"    Available days: {available_days}")
        
        # Process each day
        for day in available_days:
            print(f"    Processing Day {day}...")
            
            # Find all SNR files for this day
            snr_files = find_snr_files(snr_dir, subject, day)
            
            if not snr_files:
                print(f"      No SNR files found for {subject} Day {day}")
                continue
            
            # Separate files by measurement type
            basic_measurements = []
            snr_measurements = []
            
            for snr_file in snr_files:
                snr_data, snr_name, is_basic = load_snr_data(snr_file)
                if snr_data is not None:
                    if is_basic:
                        basic_measurements.append((snr_data, snr_name))
                    else:
                        snr_measurements.append((snr_data, snr_name))
            
            # Create dB measurements plot
            if basic_measurements:
                save_path_db = subject_output_dir / f"{subject}_Day{day}_dB_Smoothed_{window_minutes}min"
                fig_db = create_smoothed_plot(
                    basic_measurements, subject, day, save_path_db, 
                    plot_type="dB_measurements", window_minutes=window_minutes
                )
                
                # Save plots
                html_path_db = save_path_db.with_suffix('.html')
                png_path_db = save_path_db.with_suffix('.png')
                
                try:
                    fig_db.write_html(html_path_db)
                    print(f"        Saved smoothed dB plot: {html_path_db.name}")
                except Exception as e:
                    print(f"        Error saving dB HTML: {e}")
                
                try:
                    fig_db.write_image(png_path_db, width=1400, height=700, scale=2)
                    print(f"        Saved static dB plot: {png_path_db.name}")
                except Exception as e:
                    print(f"        Note: PNG export requires kaleido package")
            
            # Create SNR measurements plot
            if snr_measurements:
                save_path_snr = subject_output_dir / f"{subject}_Day{day}_SNR_Smoothed_{window_minutes}min"
                fig_snr = create_smoothed_plot(
                    snr_measurements, subject, day, save_path_snr, 
                    plot_type="SNR", window_minutes=window_minutes
                )
                
                # Save plots
                html_path_snr = save_path_snr.with_suffix('.html')
                png_path_snr = save_path_snr.with_suffix('.png')
                
                try:
                    fig_snr.write_html(html_path_snr)
                    print(f"        Saved smoothed SNR plot: {html_path_snr.name}")
                except Exception as e:
                    print(f"        Error saving SNR HTML: {e}")
                
                try:
                    fig_snr.write_image(png_path_snr, width=1400, height=700, scale=2)
                    print(f"        Saved static SNR plot: {png_path_snr.name}")
                except Exception as e:
                    print(f"        Note: PNG export requires kaleido package")
        
        # Create combined days plot if multiple days exist
        if len(available_days) > 1:
            print(f"    Creating Combined Days smoothed plot...")
            
            # Collect all measurements across days
            all_basic_measurements = []
            all_snr_measurements = []
            
            for day in available_days:
                snr_files = find_snr_files(snr_dir, subject, day)
                
                for snr_file in snr_files:
                    snr_data, snr_name, is_basic = load_snr_data(snr_file)
                    if snr_data is not None:
                        # Group measurements by base name to combine across days
                        base_name = snr_name.replace(" (smoothed)", "").replace(" (raw)", "")

                        if is_basic:
                            # Check if we already have this measurement type
                            existing_idx = None
                            for idx, (existing_data, existing_name) in enumerate(all_basic_measurements):
                                existing_base = existing_name.replace(" Day 1", "").replace(" Day 2", "").replace(" Day 3", "")
                                if existing_base == base_name:
                                    existing_idx = idx
                                    break
                            
                            if existing_idx is not None:
                                # Combine with existing measurement data
                                existing_data, existing_name = all_basic_measurements[existing_idx]
                                combined_data = pd.concat([existing_data, snr_data], ignore_index=True)
                                all_basic_measurements[existing_idx] = (combined_data, base_name)
                            else:
                                # First occurrence of this measurement type
                                all_basic_measurements.append((snr_data, base_name))
                        else:
                            # Check if we already have this measurement type  
                            existing_idx = None
                            for idx, (existing_data, existing_name) in enumerate(all_snr_measurements):
                                existing_base = existing_name.replace(" Day 1", "").replace(" Day 2", "").replace(" Day 3", "")
                                if existing_base == base_name:
                                    existing_idx = idx
                                    break
                            
                            if existing_idx is not None:
                                # Combine with existing measurement data
                                existing_data, existing_name = all_snr_measurements[existing_idx]
                                combined_data = pd.concat([existing_data, snr_data], ignore_index=True)
                                all_snr_measurements[existing_idx] = (combined_data, base_name)
                            else:
                                # First occurrence of this measurement type
                                all_snr_measurements.append((snr_data, base_name))
            
            # Create combined plots
            if all_basic_measurements:
                save_path_combined_db = subject_output_dir / f"{subject}_Combined_Days_dB_Smoothed_{window_minutes}min"
                fig_combined_db = create_smoothed_plot(
                    all_basic_measurements, subject, "Combined", save_path_combined_db,
                    plot_type="dB_measurements", window_minutes=window_minutes
                )
                
                html_path = save_path_combined_db.with_suffix('.html')
                fig_combined_db.write_html(html_path)
                print(f"        Saved combined dB plot: {html_path.name}")
            
            if all_snr_measurements:
                save_path_combined_snr = subject_output_dir / f"{subject}_Combined_Days_SNR_Smoothed_{window_minutes}min"
                fig_combined_snr = create_smoothed_plot(
                    all_snr_measurements, subject, "Combined", save_path_combined_snr,
                    plot_type="SNR", window_minutes=window_minutes
                )
                
                html_path = save_path_combined_snr.with_suffix('.html')
                fig_combined_snr.write_html(html_path)
                print(f"        Saved combined SNR plot: {html_path.name}")
    
    print(f"\nAll smoothed plots completed!")
    print(f"Plots saved in: {output_base_dir}")


def main():
    parser = argparse.ArgumentParser(description='Create smoothed SNR plots without activity data')
    parser.add_argument('--subjects', type=str, 
                       help='Subjects to process (e.g., "S1,S5,S10" or "S1-S5")')
    parser.add_argument('--days', nargs='+', 
                       help='Days to process (e.g., 1 2)')
    parser.add_argument('--window-minutes', type=int, default=15,
                       help='Smoothing window in minutes (default: 15)')
    
    args = parser.parse_args()
    
    # Parse subjects
    target_subjects = parse_subject_range(args.subjects) if args.subjects else None
    
    # Get base directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent / "outputs"
    
    print(f"Looking for SNR plots in: {base_dir / 'SNR_Interactive_Plots'}")
    
    # Process plots
    process_smoothed_plots(
        base_dir=base_dir,
        subjects=target_subjects,
        days=args.days,
        window_minutes=args.window_minutes
    )


if __name__ == "__main__":
    main()