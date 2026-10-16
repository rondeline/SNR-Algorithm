import pandas as pd
import os
from datetime import datetime, timedelta
import sys
import re
import importlib
import argparse

# Add the current directory to Python path to import the analyzer
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

import noEMA_sleep_recording_analyzer
importlib.reload(noEMA_sleep_recording_analyzer)
from noEMA_sleep_recording_analyzer import NoEMASleepRecordingAnalyzer

def extract_subject_id(filename):
    """
    Extract subject ID from filename (e.g., 'S26' from 'S26_Day1.csv')
    
    Args:
        filename (str): Input filename
        
    Returns:
        str: Subject ID
    """
    # Remove extension first
    name_without_ext = filename.replace('.csv', '')
    
    # Try to match various patterns
    patterns = [
        r'(S\d+)_Day\d+',  # S26_Day1
        r'(S\d+)_day\d+',  # S26_day1 (lowercase)
        r'Subject_(\d+)',  # Subject_1
        r'(S\d+)',         # S1, S26, etc.
        r's(\d+)',         # s1 (lowercase)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name_without_ext, re.IGNORECASE)
        if match:
            if pattern.startswith(r'Subject_'):
                return f"S{match.group(1)}"
            else:
                return match.group(1).upper()
    
    # If no pattern matches, use the filename without extension
    return name_without_ext

def get_recording_files(base_folder):
    """
    Find all recording CSV files.
    
    Args:
        base_folder (str): Path to folder containing CSV files
        
    Returns:
        dict: Dictionary mapping subject IDs to their recording files
    """
    subject_files = {}
    
    if not os.path.exists(base_folder):
        print(f"Error: Base folder {base_folder} does not exist")
        return subject_files
    
    # Look for CSV files directly in the folder
    for item in os.listdir(base_folder):
        if item.endswith('.csv'):
            file_path = os.path.join(base_folder, item)
            subject_id = extract_subject_id(item)
            
            if subject_id:
                if subject_id not in subject_files:
                    subject_files[subject_id] = []
                subject_files[subject_id].append(file_path)
                print(f"Found recording file: {file_path} -> {subject_id}")
    
    return subject_files

def run_noema_analysis(rec_file, output_dir):
    """
    Run noEMA analysis on a single recording file.
    
    Args:
        rec_file (str): Path to the recording CSV file
        output_dir (str): Directory to save output files
    """
    print(f"Running noEMA analysis with:")
    print(f"Recording file: {rec_file}")
    
    # Extract subject info from filename
    subject_id = extract_subject_id(os.path.basename(rec_file))
    
    # Determine day suffix
    filename = os.path.basename(rec_file)
    if "Day1" in filename or "day1" in filename:
        day_suffix = "Day1"
    elif "Day2" in filename or "day2" in filename:
        day_suffix = "Day2"
    else:
        day_suffix = "Day1"  # Default assumption
    
    # Create needed output subdirectories
    filtered_dir = os.path.join(output_dir, "filtered_data")
    features_dir = os.path.join(output_dir, "features")
    segments_dir = os.path.join(output_dir, "segments")
    summaries_dir = os.path.join(output_dir, "summaries")
    
    # Create subject-specific directory
    subject_dir = os.path.join(output_dir, "subjects", subject_id)
    subject_filtered_dir = os.path.join(subject_dir, "filtered_data")
    subject_features_dir = os.path.join(subject_dir, "features")
    subject_segments_dir = os.path.join(subject_dir, "segments")
    
    # Create all directories
    for directory in [filtered_dir, features_dir, segments_dir, summaries_dir, 
                     subject_dir, subject_filtered_dir, subject_features_dir, subject_segments_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # Create analyzer instance
    analyzer = NoEMASleepRecordingAnalyzer(rec_file)
    
    # Run analysis steps
    analyzer.identify_sleep_start_for_no_ema()
    analyzer.mark_first_five_minutes_invalid()
    
    # Generate output filenames
    filtered_output = os.path.join(filtered_dir, f"{subject_id}_{day_suffix}_filtered.csv")
    features_output = os.path.join(features_dir, f"{subject_id}_{day_suffix}_features.csv")
    segments_output = os.path.join(segments_dir, f"{subject_id}_{day_suffix}_segments")
    
    # Generate subject-specific output filenames
    subject_filtered_output = os.path.join(subject_filtered_dir, f"{subject_id}_{day_suffix}_filtered.csv")
    subject_features_output = os.path.join(subject_features_dir, f"{subject_id}_{day_suffix}_features.csv")
    subject_segments_output = os.path.join(subject_segments_dir, f"{subject_id}_{day_suffix}_segments")
    
    # Save results
    analyzer.save_filtered_data(filtered_output)
    analyzer.save_filtered_data(subject_filtered_output)
    
    feature_df = analyzer.calculate_intervals_and_features()
    analyzer.save_feature_data(feature_df, features_output)
    analyzer.save_feature_data(feature_df, subject_features_output)
    
    # Create segments file (covers entire recording range)
    create_segments_file(analyzer.rec_df, feature_df, segments_output)
    create_segments_file(analyzer.rec_df, feature_df, subject_segments_output)
    
    # Create summary
    create_summary_file(feature_df, subject_id, day_suffix, summaries_dir, subject_dir)
    
    print(f"Analysis complete for {subject_id} {day_suffix}")


def create_segments_file(rec_df, feature_df, output_file):
    """
    Create a segment file from after the first 5 minutes to the last possible segment.
    Ignores sleep detection setup.
    """
    if rec_df.empty:
        print(f"Warning: No recording data to create segments file")
        return
    
    # Find the start time after first 5 minutes (where Valid == 'Yes')
    valid_data = rec_df[rec_df['Valid'] == 'Yes']
    
    if valid_data.empty:
        print(f"Warning: No valid data found for segments file")
        return
    
    # Start from first valid time (after 5-minute setup period)
    start_time = valid_data['Clock_Time'].min()
    
    # End at the last timestamp in the recording (regardless of validity or sleep)
    end_time = rec_df['Clock_Time'].max()
    
    # Create a single segment covering the valid recording period
    # Get the full range of valid recording using Elapsed_Time
    onset = valid_data['Elapsed_Time'].min()
    offset = valid_data['Elapsed_Time'].max()

    # Add audio duration buffer (300 seconds = 5 minutes)
    audio_duration = 300
    offset += audio_duration

    # Create single segment covering entire valid recording
    segments_df = pd.DataFrame({
        'Segment': [1],
        'Onset': [onset],
        'Offset': [offset]
    })

    # Save in multiple formats
    output_base = output_file.rsplit('.', 1)[0] if output_file.endswith(('.csv', '.xlsx', '.txt')) else output_file

    segments_df.to_csv(output_base + '.csv', index=False, float_format='%.1f')
    segments_df.to_excel(output_base + '.xlsx', index=False, float_format='%.1f')
    segments_df.to_csv(output_base + '.txt', index=False, sep='\t', float_format='%.1f')
    print(f"Segments file saved: {output_file}.csv (from {start_time} to {end_time})")


def create_summary_file(feature_df, subject_id, day_suffix, summaries_dir, subject_dir):
    """
    Create a human-readable summary file.
    """
    summary_output = os.path.join(summaries_dir, f"{subject_id}_{day_suffix}_summary.txt")
    subject_summary_output = os.path.join(subject_dir, f"{subject_id}_{day_suffix}_summary.txt")
    
    if feature_df.empty:
        summary_text = f"No valid data found for {subject_id} {day_suffix}\n"
    else:
        # Get summary row
        summary_row = feature_df[feature_df['Primary Activity'] == 'SUMMARY']
        intervals_row = feature_df[feature_df['Primary Activity'] == 'VALID INTERVALS']
        
        if not summary_row.empty:
            summary = summary_row.iloc[0]
            
            summary_text = f"""
=== {subject_id} {day_suffix} Analysis Summary (No EMA) ===

Total AWC: {summary['AWC']:.1f}
Total Turn Count: {summary['Turn Count']:.1f}
Total Child Vocalizations: {summary['Child Vocalization Count']:.1f}
Total MAN Words: {summary['MAN Word Count']:.1f}
Total FAN Words: {summary['FAN Word Count']:.1f}

Rates per Hour:
- AWC per Hour: {summary['AWC per Hour']:.2f}
- Child Vocalizations per Hour: {summary['Child Vocalizations per Hour']:.2f}
- Turn Count per Hour: {summary['Turn Count per Hour']:.2f}
- MAN Words per Hour: {summary['MAN Words per Hour']:.2f}
- FAN Words per Hour: {summary['FAN Words per Hour']:.2f}

Rates per Minute:
- AWC per Minute: {summary['AWC per Minute']:.2f}
- Child Vocalizations per Minute: {summary['Child Vocalizations per Minute']:.2f}
- Turn Count per Minute: {summary['Turn Count per Minute']:.2f}
- MAN Words per Minute: {summary['MAN Words per Minute']:.2f}
- FAN Words per Minute: {summary['FAN Words per Minute']:.2f}

Total Recording Time: {summary['Total Time (seconds)']:.0f} seconds ({summary['Total Time (seconds)']/3600:.2f} hours)

"""
            
            if not intervals_row.empty:
                intervals = intervals_row.iloc[0]
                summary_text += f"Valid Intervals: {intervals['Secondary Activity']}\n"
                summary_text += f"Total Valid Duration: {intervals['Elapsed_Duration']:.1f} hours\n"
        else:
            summary_text = f"No summary data available for {subject_id} {day_suffix}\n"
    
    # Save summary to both locations
    for output_path in [summary_output, subject_summary_output]:
        with open(output_path, 'w') as f:
            f.write(summary_text)
        print(f"Summary saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run batch noEMA analysis on recording files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run analysis on all CSV files in a directory
    python run_batch_noEMA_analysis.py --input_dir "Z:/path/to/csvs" --output_dir "Z:/outputs"
    
    # Process specific subjects
    python run_batch_noEMA_analysis.py --input_dir "Z:/path/to/csvs" --output_dir "Z:/outputs" --subjects S26,S30
        """
    )
    
    parser.add_argument("--input_dir", required=True, 
                       help="Path to directory containing CSV files")
    parser.add_argument("--output_dir", required=True,
                       help="Path to output directory")
    parser.add_argument("--subjects", 
                       help="Comma-separated list of subjects to process (e.g., S26,S30)")
    
    args = parser.parse_args()
    
    input_dir = args.input_dir
    output_dir = args.output_dir
    target_subjects = args.subjects.split(',') if args.subjects else None
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    if target_subjects:
        print(f"Target subjects: {target_subjects}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all recording files
    subject_files = get_recording_files(input_dir)
    
    if not subject_files:
        print("No CSV files found!")
        return
    
    # Filter subjects if specified
    if target_subjects:
        filtered_files = {k: v for k, v in subject_files.items() if k in target_subjects}
        subject_files = filtered_files
    
    print(f"\nFound {len(subject_files)} subjects to process:")
    for subject_id, files in subject_files.items():
        print(f"  {subject_id}: {len(files)} file(s)")
    
    # Process each subject
    total_files = sum(len(files) for files in subject_files.values())
    processed_files = 0
    
    for subject_id, files in subject_files.items():
        print(f"\n{'='*50}")
        print(f"Processing {subject_id}")
        print(f"{'='*50}")
        
        for rec_file in files:
            processed_files += 1
            print(f"\n[{processed_files}/{total_files}] Processing: {os.path.basename(rec_file)}")
            
            try:
                run_noema_analysis(rec_file, output_dir)
                print(f" Success: {os.path.basename(rec_file)}")
            except Exception as e:
                print(f" Error processing {rec_file}: {str(e)}")
                print(f"  Continuing with next file...")
                continue
    
    print(f"\n{'='*50}")
    print(f"Batch processing complete!")
    print(f"Processed {processed_files} files")
    print(f"Results saved to: {output_dir}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()