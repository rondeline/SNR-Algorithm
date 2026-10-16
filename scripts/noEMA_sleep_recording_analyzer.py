import pandas
from datetime import datetime, timedelta
import sys
import argparse
import os

class NoEMASleepRecordingAnalyzer:
    """
    Sleep Recording Analyzer that works with original CSV format but without EMA files.
    Based on SleepActivityAnalyzer but removes all EMA dependencies.
    """
    def __init__(self, rec_file_path):
        self.rec_file_path = rec_file_path
        self.rec_df = None
        self.load_data()

    def load_data(self):
        """Load and prepare the recording data"""
        try:
            self.rec_df = pd.read_csv(self.rec_file_path)
        except FileNotFoundError:
            print(f"Error: The file {self.rec_file_path} was not found.")
            sys.exit(1)

        # Initialize required columns if they don't exist
        required_columns = ['Environment', 'Primary_Activity', 'Secondary_Activity', 'Valid']
        for col in required_columns:
            if col not in self.rec_df.columns:
                if col == 'Environment':
                    self.rec_df[col] = 'Inside'  # Default to inside
                elif col == 'Valid':
                    self.rec_df[col] = 'Yes'  # Default to valid
                else:
                    self.rec_df[col] = None  # Will be set later

        # Handle datetime conversion for Clock_Time_TZAdj
        if 'Clock_Time_TZAdj' in self.rec_df.columns:
            if self.rec_df['Clock_Time_TZAdj'].dtype == 'object':
                # It's a string, try to parse it
                try:
                    self.rec_df['Clock_Time_TZAdj'] = pd.to_datetime(self.rec_df['Clock_Time_TZAdj'])
                except Exception as e:
                    print(f"Error converting Clock_Time_TZAdj: {e}")
                    sys.exit(1)
            
            # Create Clock_Time column for compatibility
            self.rec_df['Clock_Time'] = self.rec_df['Clock_Time_TZAdj']
        elif 'Clock_Time' not in self.rec_df.columns:
            print("Error: Neither Clock_Time nor Clock_Time_TZAdj found in CSV")
            sys.exit(1)

        # Convert float columns to the appropriate type
        float_columns = ['AWC', 'Turn_Count', 'Child_Voc_Count', 'CHN',
                        'Child_Voc_Duration', 'Child_NonVoc_Duration',
                        'FAN_Word_Count', 'FAN', 'FAN_NonVoc_Duration',
                        'MAN_Word_Count', 'MAN', 'MAN_NonVoc_Duration',
                        'CXN', 'OLN', 'TVN', 'NON', 'SIL', 'FUZ']

        for col in float_columns:
            if col in self.rec_df.columns:
                self.rec_df[col] = pd.to_numeric(self.rec_df[col], errors='coerce')

        # Ensure AWC is treated as float
        if 'AWC' in self.rec_df.columns:
            self.rec_df['AWC'] = self.rec_df['AWC'].fillna(0).astype(float)

        # Set default activities for all rows
        self.rec_df['Primary_Activity'] = 'Recording'
        self.rec_df['Secondary_Activity'] = None
        self.rec_df['Environment'] = 'Inside'
        self.rec_df['Valid'] = 'Yes'

        print(f"Loaded {len(self.rec_df)} rows from {self.rec_file_path}")

    def identify_sleep_start_for_no_ema(self):
        """
        Identify sleep start using AWC pattern without EMA data.
        Looks for 3 consecutive zeros in AWC to detect sleep onset.
        """
        awc_column = 'AWC'
        zero_count = 0
        actual_sleep_start_idx = None

        # Look for sleep pattern in the latter part of the recording (after 8 PM)
        evening_cutoff = self.rec_df['Clock_Time'].min().replace(hour=20, minute=0, second=0)
        evening_rows = self.rec_df[self.rec_df['Clock_Time'] >= evening_cutoff]

        for idx in evening_rows.index:
            row = self.rec_df.loc[idx]
            awc_value = row[awc_column]

            if awc_value == 0:
                zero_count += 1
                if zero_count == 3:
                    actual_sleep_start_idx = idx - 2
                    break
            else:
                zero_count = 0

        if actual_sleep_start_idx is not None:
            self.update_sleep_periods(actual_sleep_start_idx)
            print(f"Sleep onset detected at index {actual_sleep_start_idx}")
        else:
            print("No clear sleep onset pattern detected")

    def update_sleep_periods(self, actual_sleep_start_idx):
        """Update activities to mark sleep periods"""
        actual_sleep_start_time = self.rec_df.loc[actual_sleep_start_idx, 'Clock_Time']
        
        # Mark everything after sleep start as sleeping
        sleep_mask = self.rec_df['Clock_Time'] >= actual_sleep_start_time
        self.rec_df.loc[sleep_mask, 'Primary_Activity'] = 'Sleeping'
        self.rec_df.loc[sleep_mask, 'Secondary_Activity'] = None
        self.rec_df.loc[sleep_mask, 'Environment'] = 'Inside'
        
        print(f"Marked sleep period starting from {actual_sleep_start_time}")

    def mark_first_five_minutes_invalid(self):
        """Mark the first 5 minutes as invalid for equipment setup"""
        if not self.rec_df.empty:
            # Find first valid time
            valid_rows = self.rec_df[self.rec_df['Primary_Activity'] == 'Recording']
            if not valid_rows.empty:
                first_valid_time = valid_rows['Clock_Time'].min()
                first_recording_time = self.rec_df['Clock_Time'].min()

                # Only mark as invalid if the first valid interval starts at the beginning
                if first_valid_time == first_recording_time:
                    cutoff_time = first_valid_time + timedelta(minutes=5)
                    
                    # Mark first 5 minutes as invalid
                    setup_mask = (
                        (self.rec_df['Clock_Time'] >= first_valid_time) &
                        (self.rec_df['Clock_Time'] < cutoff_time) &
                        (self.rec_df['Primary_Activity'] == 'Recording')
                    )
                    self.rec_df.loc[setup_mask, 'Valid'] = 'No'
                    
                    print(f"Marked first 5 minutes as invalid: {first_valid_time} to {cutoff_time}")

    def save_filtered_data(self, output_file_path):
        """Save filtered data with validity markings"""
        # Add Valid column based on the criteria
        self.rec_df['Valid'] = 'Yes'

        # Mark invalid data based on sleep and activity criteria
        invalid_mask = (
            (self.rec_df['Primary_Activity'].isin(['Sleeping', 'Activity-less Sleeping', 'Nap'])) |
            (self.rec_df['Secondary_Activity'] == 'Nap') |
            (self.rec_df['Environment'] == 'Outside') |
            (self.rec_df['Primary_Activity'].isna()) |
            (self.rec_df['Primary_Activity'].str.strip() == '') |
            (self.rec_df['Primary_Activity'] == 'nan')
        )
        self.rec_df.loc[invalid_mask, 'Valid'] = 'No'

        # Convert activities to string before saving
        activity_cols = ['Primary_Activity', 'Secondary_Activity']
        for col in activity_cols:
            self.rec_df[col] = self.rec_df[col].fillna('').astype(str)
            # Replace 'nan' string with empty string
            self.rec_df[col] = self.rec_df[col].replace('nan', '')

        self.rec_df.to_csv(output_file_path, index=False)
        print(f"Filtered data saved to: {output_file_path}")

    def calculate_intervals_and_features(self):
        """Calculate features using sophisticated interval analysis similar to SleepActivityAnalyzer"""
        feature_data = []
        first_date = self.rec_df['Clock_Time'].iloc[0].date()

        # Create 2-hour fixed intervals (6AM to 10PM)
        fixed_intervals = []
        for hour in range(6, 23, 2):
            start_time = pd.Timestamp.combine(
                first_date,
                pd.Timestamp(f"{hour:02d}:00").time()
            )
            end_time = start_time + timedelta(hours=2)
            fixed_intervals.append((start_time, end_time))

        # Calculate features for each interval
        for start_time, end_time in fixed_intervals:
            interval_data = self.rec_df[
                (self.rec_df['Clock_Time'] >= start_time) & 
                (self.rec_df['Clock_Time'] < end_time)
            ]
            
            if not interval_data.empty:
                features = self.generate_feature_dict(start_time, end_time, interval_data)
                feature_data.append(features)

        # Add summary statistics
        if feature_data:
            summary_dict = self.calculate_summary_statistics(feature_data)
            feature_data.append(summary_dict)
            
            # Add valid intervals info
            valid_intervals_dict = self.format_valid_intervals(feature_data[:-1])  # Exclude summary
            feature_data.append(valid_intervals_dict)

        return pd.DataFrame(feature_data)

    def generate_feature_dict(self, start_time, end_time, interval_data):
        """Generate feature dictionary for a time interval"""
        # Calculate duration
        total_duration = (end_time - start_time).total_seconds() / 3600  # hours
        total_duration_minutes = total_duration * 60

        # Only include valid data for calculations
        valid_data = interval_data[interval_data['Valid'] == 'Yes']
        
        if valid_data.empty:
            return self._create_empty_features(start_time, end_time)

        # Calculate sums
        awc_sum = valid_data['AWC'].sum()
        turn_count_sum = valid_data['Turn_Count'].sum() if 'Turn_Count' in valid_data.columns else 0
        child_voc_count_sum = valid_data['Child_Voc_Count'].sum() if 'Child_Voc_Count' in valid_data.columns else 0
        man_word_count_sum = valid_data['MAN_Word_Count'].sum() if 'MAN_Word_Count' in valid_data.columns else 0
        fan_word_count_sum = valid_data['FAN_Word_Count'].sum() if 'FAN_Word_Count' in valid_data.columns else 0

        # Duration sums
        child_voc_duration_sum = valid_data['Child_Voc_Duration'].sum() if 'Child_Voc_Duration' in valid_data.columns else 0
        child_nonvoc_duration_sum = valid_data['Child_NonVoc_Duration'].sum() if 'Child_NonVoc_Duration' in valid_data.columns else 0
        man_sum = valid_data['MAN'].sum() if 'MAN' in valid_data.columns else 0
        fan_sum = valid_data['FAN'].sum() if 'FAN' in valid_data.columns else 0
        
        # Audio category sums
        cxn_sum = valid_data['CXN'].sum() if 'CXN' in valid_data.columns else 0
        oln_sum = valid_data['OLN'].sum() if 'OLN' in valid_data.columns else 0
        tvn_sum = valid_data['TVN'].sum() if 'TVN' in valid_data.columns else 0
        non_sum = valid_data['NON'].sum() if 'NON' in valid_data.columns else 0
        sil_sum = valid_data['SIL'].sum() if 'SIL' in valid_data.columns else 0
        fuz_sum = valid_data['FUZ'].sum() if 'FUZ' in valid_data.columns else 0

        # Elapsed time calculation
        elapsed_start = (start_time - self.rec_df['Clock_Time'].min()).total_seconds() / 3600
        elapsed_end = (end_time - self.rec_df['Clock_Time'].min()).total_seconds() / 3600

        return {
            'Start Time': start_time.strftime('%H:%M:%S'),
            'End Time': end_time.strftime('%H:%M:%S'),
            'Primary Activity': 'Recording',
            'Secondary Activity': '',
            'Environment': 'Inside',
            'Valid': 'Yes',
            'Elapsed_Start': round(elapsed_start, 1),
            'Elapsed_End': round(elapsed_end, 1),
            'Elapsed_Duration': round(elapsed_end - elapsed_start, 1),
            'Child Vocalization Count': round(child_voc_count_sum, 3),
            'MAN Word Count': round(man_word_count_sum, 3),
            'FAN Word Count': round(fan_word_count_sum, 3),
            'AWC': round(awc_sum, 3),
            'Turn Count': round(turn_count_sum, 3),
            'Child Vocalization Time (seconds)': round(child_voc_duration_sum, 3),
            'Child Non-Vocalization Time (seconds)': round(child_nonvoc_duration_sum, 3),
            'MAN Duration (seconds)': round(man_sum, 3),
            'FAN Duration (seconds)': round(fan_sum, 3),
            'CXN Time (seconds)': round(cxn_sum, 3),
            'OLN Time (seconds)': round(oln_sum, 3),
            'TVN Time (seconds)': round(tvn_sum, 3),
            'NON Time (seconds)': round(non_sum, 3),
            'SIL Time (seconds)': round(sil_sum, 3),
            'FUZ Time (seconds)': round(fuz_sum, 3),
            'Child Vocalizations per Hour': round(child_voc_count_sum / total_duration, 3) if total_duration > 0 else 0,
            'MAN Words per Hour': round(man_word_count_sum / total_duration, 3) if total_duration > 0 else 0,
            'FAN Words per Hour': round(fan_word_count_sum / total_duration, 3) if total_duration > 0 else 0,
            'AWC per Hour': round(awc_sum / total_duration, 3) if total_duration > 0 else 0,
            'Turn Count per Hour': round(turn_count_sum / total_duration, 3) if total_duration > 0 else 0,
            'Child Vocalizations per Minute': round(child_voc_count_sum / total_duration_minutes, 3) if total_duration_minutes > 0 else 0,
            'MAN Words per Minute': round(man_word_count_sum / total_duration_minutes, 3) if total_duration_minutes > 0 else 0,
            'FAN Words per Minute': round(fan_word_count_sum / total_duration_minutes, 3) if total_duration_minutes > 0 else 0,
            'AWC per Minute': round(awc_sum / total_duration_minutes, 3) if total_duration_minutes > 0 else 0,
            'Turn Count per Minute': round(turn_count_sum / total_duration_minutes, 3) if total_duration_minutes > 0 else 0,
            'Total Time (seconds)': round(len(valid_data) * 5, 3),  # Assuming 5-second segments
            'Time Difference (seconds)': 0  # No difference calculation needed for this version
        }

    def _create_empty_features(self, start_time, end_time):
        """Create empty feature dictionary when no valid data exists"""
        elapsed_start = (start_time - self.rec_df['Clock_Time'].min()).total_seconds() / 3600
        elapsed_end = (end_time - self.rec_df['Clock_Time'].min()).total_seconds() / 3600
        
        return {
            'Start Time': start_time.strftime('%H:%M:%S'),
            'End Time': end_time.strftime('%H:%M:%S'),
            'Primary Activity': 'Recording',
            'Secondary Activity': 'No Valid Recording',
            'Environment': 'Inside',
            'Valid': 'No',
            'Elapsed_Start': round(elapsed_start, 1),
            'Elapsed_End': round(elapsed_end, 1),
            'Elapsed_Duration': round(elapsed_end - elapsed_start, 1),
            'Child Vocalization Count': 0, 'MAN Word Count': 0, 'FAN Word Count': 0,
            'AWC': 0, 'Turn Count': 0,
            'Child Vocalization Time (seconds)': 0, 'Child Non-Vocalization Time (seconds)': 0,
            'MAN Duration (seconds)': 0, 'FAN Duration (seconds)': 0,
            'CXN Time (seconds)': 0, 'OLN Time (seconds)': 0, 'TVN Time (seconds)': 0,
            'NON Time (seconds)': 0, 'SIL Time (seconds)': 0, 'FUZ Time (seconds)': 0,
            'Child Vocalizations per Hour': 0, 'MAN Words per Hour': 0, 'FAN Words per Hour': 0,
            'AWC per Hour': 0, 'Turn Count per Hour': 0,
            'Child Vocalizations per Minute': 0, 'MAN Words per Minute': 0, 'FAN Words per Minute': 0,
            'AWC per Minute': 0, 'Turn Count per Minute': 0,
            'Total Time (seconds)': 0, 'Time Difference (seconds)': 0
        }

    def calculate_summary_statistics(self, feature_data):
        """Calculate summary statistics across all intervals"""
        if not feature_data:
            return self._create_empty_summary()

        # Aggregate across all valid intervals
        total_child_voc_count = sum(row['Child Vocalization Count'] for row in feature_data)
        total_man_word_count = sum(row['MAN Word Count'] for row in feature_data)
        total_fan_word_count = sum(row['FAN Word Count'] for row in feature_data)
        total_awc = sum(row['AWC'] for row in feature_data)
        total_turn_count = sum(row['Turn Count'] for row in feature_data)
        
        # Duration calculations
        total_actual_duration = sum(row['Total Time (seconds)'] for row in feature_data)
        total_theoretical_duration = len(feature_data) * 2 * 3600  # 2 hours per interval in seconds
        total_duration_hours = total_actual_duration / 3600
        total_duration_minutes = total_actual_duration / 60

        return {
            'Start Time': None, 'End Time': None,
            'Primary Activity': 'SUMMARY', 'Secondary Activity': 'Overall Statistics',
            'Environment': 'Inside', 'Valid': 'Summary',
            'Elapsed_Start': None, 'Elapsed_End': None, 'Elapsed_Duration': None,
            'Child Vocalization Count': round(total_child_voc_count, 3),
            'MAN Word Count': round(total_man_word_count, 3),
            'FAN Word Count': round(total_fan_word_count, 3),
            'AWC': round(total_awc, 3),
            'Turn Count': round(total_turn_count, 3),
            'Child Vocalization Time (seconds)': sum(row['Child Vocalization Time (seconds)'] for row in feature_data),
            'Child Non-Vocalization Time (seconds)': sum(row['Child Non-Vocalization Time (seconds)'] for row in feature_data),
            'MAN Duration (seconds)': sum(row['MAN Duration (seconds)'] for row in feature_data),
            'FAN Duration (seconds)': sum(row['FAN Duration (seconds)'] for row in feature_data),
            'CXN Time (seconds)': sum(row['CXN Time (seconds)'] for row in feature_data),
            'OLN Time (seconds)': sum(row['OLN Time (seconds)'] for row in feature_data),
            'TVN Time (seconds)': sum(row['TVN Time (seconds)'] for row in feature_data),
            'NON Time (seconds)': sum(row['NON Time (seconds)'] for row in feature_data),
            'SIL Time (seconds)': sum(row['SIL Time (seconds)'] for row in feature_data),
            'FUZ Time (seconds)': sum(row['FUZ Time (seconds)'] for row in feature_data),
            'Child Vocalizations per Hour': round(total_child_voc_count / total_duration_hours, 3) if total_duration_hours > 0 else 0,
            'MAN Words per Hour': round(total_man_word_count / total_duration_hours, 3) if total_duration_hours > 0 else 0,
            'FAN Words per Hour': round(total_fan_word_count / total_duration_hours, 3) if total_duration_hours > 0 else 0,
            'AWC per Hour': round(total_awc / total_duration_hours, 3) if total_duration_hours > 0 else 0,
            'Turn Count per Hour': round(total_turn_count / total_duration_hours, 3) if total_duration_hours > 0 else 0,
            'Child Vocalizations per Minute': round(total_child_voc_count / total_duration_minutes, 3) if total_duration_minutes > 0 else 0,
            'MAN Words per Minute': round(total_man_word_count / total_duration_minutes, 3) if total_duration_minutes > 0 else 0,
            'FAN Words per Minute': round(total_fan_word_count / total_duration_minutes, 3) if total_duration_minutes > 0 else 0,
            'AWC per Minute': round(total_awc / total_duration_minutes, 3) if total_duration_minutes > 0 else 0,
            'Turn Count per Minute': round(total_turn_count / total_duration_minutes, 3) if total_duration_minutes > 0 else 0,
            'Total Time (seconds)': round(total_actual_duration, 3),
            'Time Difference (seconds)': round(total_theoretical_duration - total_actual_duration, 3)
        }

    def _create_empty_summary(self):
        """Create empty summary when no valid data exists"""
        return {
            'Start Time': None, 'End Time': None,
            'Primary Activity': 'SUMMARY', 'Secondary Activity': 'No Valid Recording',
            'Environment': 'Inside', 'Valid': 'Summary',
            'Elapsed_Start': None, 'Elapsed_End': None, 'Elapsed_Duration': None,
            'Child Vocalization Count': 0, 'MAN Word Count': 0, 'FAN Word Count': 0,
            'AWC': 0, 'Turn Count': 0,
            'Child Vocalization Time (seconds)': 0, 'Child Non-Vocalization Time (seconds)': 0,
            'MAN Duration (seconds)': 0, 'FAN Duration (seconds)': 0,
            'CXN Time (seconds)': 0, 'OLN Time (seconds)': 0, 'TVN Time (seconds)': 0,
            'NON Time (seconds)': 0, 'SIL Time (seconds)': 0, 'FUZ Time (seconds)': 0,
            'Child Vocalizations per Hour': 0, 'MAN Words per Hour': 0, 'FAN Words per Hour': 0,
            'AWC per Hour': 0, 'Turn Count per Hour': 0,
            'Child Vocalizations per Minute': 0, 'MAN Words per Minute': 0, 'FAN Words per Minute': 0,
            'AWC per Minute': 0, 'Turn Count per Minute': 0,
            'Total Time (seconds)': 0, 'Time Difference (seconds)': 0
        }

    def format_valid_intervals(self, valid_data):
        """Format the valid intervals as a single row entry"""
        if not valid_data:
            intervals_text = "No valid intervals"
            total_valid_duration = 0
        else:
            # Format intervals
            intervals = []
            total_valid_duration = 0
            for row in valid_data:
                if row['Valid'] == 'Yes':
                    start_time = row['Start Time']
                    end_time = row['End Time']
                    intervals.append(f"{start_time}-{end_time}")
                    total_valid_duration += row['Elapsed_Duration']
            
            intervals_text = "; ".join(intervals) if intervals else "No valid intervals"

        return {
            'Start Time': None, 'End Time': None,
            'Primary Activity': 'VALID INTERVALS', 'Secondary Activity': intervals_text,
            'Environment': 'Inside', 'Valid': 'Summary',
            'Elapsed_Start': None, 'Elapsed_End': None, 'Elapsed_Duration': round(total_valid_duration, 1),
            'Child Vocalization Count': 0, 'MAN Word Count': 0, 'FAN Word Count': 0,
            'AWC': 0, 'Turn Count': 0,
            'Child Vocalization Time (seconds)': 0, 'Child Non-Vocalization Time (seconds)': 0,
            'MAN Duration (seconds)': 0, 'FAN Duration (seconds)': 0,
            'CXN Time (seconds)': 0, 'OLN Time (seconds)': 0, 'TVN Time (seconds)': 0,
            'NON Time (seconds)': 0, 'SIL Time (seconds)': 0, 'FUZ Time (seconds)': 0,
            'Child Vocalizations per Hour': 0, 'MAN Words per Hour': 0, 'FAN Words per Hour': 0,
            'AWC per Hour': 0, 'Turn Count per Hour': 0,
            'Child Vocalizations per Minute': 0, 'MAN Words per Minute': 0, 'FAN Words per Minute': 0,
            'AWC per Minute': 0, 'Turn Count per Minute': 0,
            'Total Time (seconds)': 0, 'Time Difference (seconds)': 0
        }

    def save_feature_data(self, feature_df, output_features_file_path):
        """Save feature data to CSV"""
        # Convert activity columns to string
        activity_cols = ['Primary Activity', 'Secondary Activity']
        for col in activity_cols:
            if col in feature_df.columns:
                feature_df[col] = feature_df[col].fillna('').astype(str)
                feature_df[col] = feature_df[col].replace('nan', '')

        feature_df.to_csv(output_features_file_path, index=False)
        print(f"Feature data saved to: {output_features_file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run NoEMASleepRecordingAnalyzer on recording CSV without EMA.")
    parser.add_argument("--rec", required=True, help="Path to the recording CSV file.")
    parser.add_argument("--output", required=True, help="Directory to store output CSV files.")

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)

    # Output filenames
    output_filtered_path = os.path.join(args.output, "filtered_noEMA_sleep.csv")
    output_features_path = os.path.join(args.output, "features_noEMA_sleep.csv")

    # Run the analyzer
    analyzer = NoEMASleepRecordingAnalyzer(args.rec)
    analyzer.identify_sleep_start_for_no_ema()
    analyzer.mark_first_five_minutes_invalid()

    analyzer.save_filtered_data(output_filtered_path)
    feature_df = analyzer.calculate_intervals_and_features()
    analyzer.save_feature_data(feature_df, output_features_path)

    print(f"\nAll done! Outputs saved to: {args.output}")