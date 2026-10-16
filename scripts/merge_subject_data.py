#!/usr/bin/env python3
"""
merge_subject_data.py - Merge subject data from new Individual_SNR output into master file

This script takes the Individual_SNR_Power_NIH_s16.xlsx file from the matlab_outputs 
and merges it into the master Individual_SNR_Power_NIH.xlsx file. It handles:
- Checking for existing subjects (by sheet names like S22_XX_r1)
- Overwriting existing subject sheets with new data
- Appending new subjects that don't exist in the master file
- Preserving all other sheets in the master file

Usage:
    python merge_subject_data.py
    python merge_subject_data.py --source "path/to/new/file.xlsx" --target "path/to/master/file.xlsx"
    python merge_subject_data.py --dry-run  # Preview changes without making them
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook, Workbook
import shutil
from datetime import datetime
from typing import Optional
import re


def extract_subject_from_sheet(sheet_name: str) -> str:
    """Extract subject ID from sheet name like 'S22_XX_r1' -> 'S22'"""
    if '_' in sheet_name and sheet_name.startswith('S'):
        return sheet_name.split('_')[0]
    return sheet_name


def get_subject_sheets(file_path: Path) -> dict:
    """Get all sheets organized by subject ID"""
    if not file_path.exists():
        return {}
    
    try:
        xl_file = pd.ExcelFile(file_path)
        subject_sheets = {}
        
        for sheet_name in xl_file.sheet_names:
            if sheet_name.startswith('S') and '_' in sheet_name:
                subject_id = extract_subject_from_sheet(sheet_name)
                if subject_id not in subject_sheets:
                    subject_sheets[subject_id] = []
                subject_sheets[subject_id].append(sheet_name)
        
        return subject_sheets
    
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {}


def copy_sheet_data(source_wb, target_wb, sheet_name: str):
    """Copy a sheet from source workbook to target workbook"""
    if sheet_name not in source_wb.sheetnames:
        print(f"Warning: Sheet '{sheet_name}' not found in source file")
        return False
    
    source_sheet = source_wb[sheet_name]
    
    # Remove existing sheet if it exists
    if sheet_name in target_wb.sheetnames:
        target_wb.remove(target_wb[sheet_name])
        print(f"  Removed existing sheet: {sheet_name}")
    
    # Create new sheet
    target_sheet = target_wb.create_sheet(sheet_name)
    
    # Copy all cell values (skip formatting to avoid StyleProxy errors)
    for row in source_sheet.iter_rows():
        for cell in row:
            target_cell = target_sheet[cell.coordinate]
            target_cell.value = cell.value
            
            # Only copy number format safely
            try:
                if cell.number_format and cell.number_format != 'General':
                    target_cell.number_format = cell.number_format
            except:
                pass  # Skip if there's any formatting issue
    
    # Copy column widths safely
    try:
        for col_letter, col_dim in source_sheet.column_dimensions.items():
            if col_dim.width:
                target_sheet.column_dimensions[col_letter].width = col_dim.width
    except:
        pass  # Skip if there's any dimension issue
    
    # Copy row heights safely
    try:
        for row_num, row_dim in source_sheet.row_dimensions.items():
            if row_dim.height:
                target_sheet.row_dimensions[row_num].height = row_dim.height
    except:
        pass  # Skip if there's any dimension issue
    
    print(f"  Copied sheet: {sheet_name}")
    return True

def get_version_file_names(version: str) -> tuple:
    """Get the appropriate file names for a given MATLAB version"""
    if version == "5.0.1":
        individual_name = "Individual_SNR_Power.xlsx"
        batch_name = "Compiled_BatchRun.xlsx"
    elif version in ["4.6", "4.3.1"]:
        individual_name = "Individual_SNR_Power.xlsx"
        batch_name = "Compiled_BatchRun.xlsx"
    else:
        print(f"Unknown version: {version}, defaulting to 5.0.1 naming")
        individual_name = "Individual_SNR_Power.xlsx"
        batch_name = "Compiled_BatchRun.xlsx"
    
    return individual_name, batch_name

def filter_subject_data(source_file: Path, target_file: Path, subject_filter: Optional[str] = None):
    """Handle subject-specific data merging for Individual_SNR file."""
    if not source_file.exists():
        print(f"Source file not found: {source_file}")
        return
    
    try:
        # Load source workbook
        wb_source = load_workbook(source_file)
        
        # If target doesn't exist, just copy everything
        if not target_file.exists():
            shutil.copy2(source_file, target_file)
            print(f"Created new file: {target_file}")
            wb_source.close()
            return
        
        # Load target workbook
        wb_target = load_workbook(target_file)
        
        # Get sheets to process
        if subject_filter:
            # Only process sheets for the specified subject
            sheets_to_process = [sheet for sheet in wb_source.sheetnames 
                               if sheet.startswith(f"{subject_filter}_")]
        else:
            sheets_to_process = wb_source.sheetnames
        
        # Process each sheet
        for sheet_name in sheets_to_process:
            if sheet_name in wb_target.sheetnames:
                # Remove existing sheet
                wb_target.remove(wb_target[sheet_name])
                print(f"  Replacing sheet: {sheet_name}")
            else:
                print(f"  Adding new sheet: {sheet_name}")
            
            # Copy sheet from source to target
            source_sheet = wb_source[sheet_name]
            target_sheet = wb_target.create_sheet(sheet_name)
            
            # Copy all cells (avoid style copying to prevent errors)
            for row in source_sheet.iter_rows():
                for cell in row:
                    target_sheet[cell.coordinate].value = cell.value
        
        # Save the target workbook
        wb_target.save(target_file)
        wb_source.close()
        wb_target.close()
        print(f"Updated: {target_file}")
        
    except Exception as e:
        print(f"Error in filter_subject_data: {e}")
        # Fallback to simple copy if filtering fails
        try:
            if wb_source:
                wb_source.close()
            if wb_target:
                wb_target.close()
        except:
            pass
        
        try:
            shutil.copy2(source_file, target_file)
            print(f"Fallback: Copied entire file due to error")
        except Exception as e2:
            print(f"Fallback copy also failed: {e2}")
            raise


def merge_compiled_batch_data(source_file: Path, target_file: Path, dry_run: bool = False) -> bool:
    """
    Merge Compiled_BatchRun data from source to target.
    
    Args:
        source_file: Path to Compiled_BatchRun_NIH_study.xlsx (from matlab_outputs)
        target_file: Path to Compiled_BatchRun_NIH_study.xlsx (master file)
        dry_run: If True, only preview changes without making them
    
    Returns:
        bool: True if successful, False otherwise
    """
    import re  # Add missing import
    
    try:
        # Check if source file exists
        if not source_file.exists():
            print(f"Source Compiled_BatchRun file not found: {source_file}")
            return True  # Not an error if file doesn't exist
        
        print(f"\n{'='*60}")
        print(f"MERGING COMPILED BATCH DATA")
        print(f"{'='*60}")
        print(f"Source: {source_file}")
        print(f"Target: {target_file}")
        
        # Read source file - handle both Excel and CSV
        if source_file.suffix.lower() == '.xlsx':
            # First, let's examine the Excel file structure
            xl_file = pd.ExcelFile(source_file)
            print(f"Available sheets: {xl_file.sheet_names}")
            
            if not xl_file.sheet_names:
                print("No sheets found in Excel file - skipping merge")
                return True
            
            # Look for the "Compiled_BatchRun" sheet specifically
            data_sheet_name = None
            if "Compiled_BatchRun" in xl_file.sheet_names:
                data_sheet_name = "Compiled_BatchRun"
                print(f"Found Compiled_BatchRun sheet - using this for data")
            else:
                # Fallback to second sheet if it exists, or first sheet
                if len(xl_file.sheet_names) > 1:
                    data_sheet_name = xl_file.sheet_names[1] 
                    print(f"Using second sheet: {data_sheet_name}")
                else:
                    data_sheet_name = xl_file.sheet_names[0]
                    print(f"Using first sheet: {data_sheet_name}")
            
            # Read the correct sheet to examine structure  
            temp_df = pd.read_excel(source_file, sheet_name=data_sheet_name, header=None, nrows=10)
            print(f"First 10 rows of sheet '{data_sheet_name}':")
            print(temp_df)
            
            # Check if this sheet is effectively empty
            if temp_df.empty or temp_df.shape[0] == 0:
                print(f"Sheet '{data_sheet_name}' appears to be empty - skipping merge")
                return True
            
            # Try reading with different approaches
            try:
                # First try: assume first row is header, first column is index
                source_df = pd.read_excel(source_file, sheet_name=data_sheet_name, header=0, index_col=0)
                if source_df.empty and len(xl_file.sheet_names) > 1:
                    # If first approach failed and we have multiple sheets, try without index_col
                    source_df = pd.read_excel(source_file, sheet_name=data_sheet_name, header=0)
                    if not source_df.empty and len(source_df.columns) > 0:
                        source_df = source_df.set_index(source_df.columns[0])
            except Exception as e:
                print(f"Error reading Excel sheet '{data_sheet_name}': {e}")
                print("Skipping Compiled_BatchRun merge due to file format issues")
                return True
                    
            print(f"Shape after reading: {source_df.shape}")
            if not source_df.empty:
                print(f"Columns: {list(source_df.columns)}")
                print(f"Index (first few): {list(source_df.index[:5])}")
        else:
            source_df = pd.read_csv(source_file, index_col=0)  # First column as index (data labels)
        
        # Check if we have any meaningful data
        if source_df.empty or len(source_df.columns) == 0:
            print("No meaningful data found in source file")
            print("This is normal when processing individual subjects - Compiled_BatchRun requires all subjects")
            return True
        
        print(f"Source subjects found: {list(source_df.columns)}")
        
        # Create target file if it doesn't exist
        if not target_file.exists():
            print(f"Target file doesn't exist, creating new one: {target_file}")
            if not dry_run:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                # Save in appropriate format
                if target_file.suffix.lower() == '.xlsx':
                    # For new Excel files, create with the Compiled_BatchRun sheet
                    with pd.ExcelWriter(target_file, engine='openpyxl') as writer:
                        source_df.to_excel(writer, sheet_name='Compiled_BatchRun', index=True)
                else:
                    source_df.to_csv(target_file, index=True)
            print(f"Created new target file with {len(source_df.columns)} subjects")
            return True
        
        # Read target file - handle both Excel and CSV  
        if target_file.suffix.lower() == '.xlsx':
            target_xl_file = pd.ExcelFile(target_file)
            print(f"Target sheets: {target_xl_file.sheet_names}")
            
            # Look for the "Compiled_BatchRun" sheet in target file too
            target_sheet_name = None
            if "Compiled_BatchRun" in target_xl_file.sheet_names:
                target_sheet_name = "Compiled_BatchRun"
            elif len(target_xl_file.sheet_names) > 1:
                target_sheet_name = target_xl_file.sheet_names[1] 
            else:
                target_sheet_name = target_xl_file.sheet_names[0]
            
            target_df = pd.read_excel(target_file, sheet_name=target_sheet_name, header=0, index_col=0)
        else:
            target_df = pd.read_csv(target_file, index_col=0)  # First column as index (data labels)
        print(f"Target subjects before merge: {list(target_df.columns)}")
        
        # Track changes
        subjects_updated = []
        subjects_added = []
        
        # Process each subject column from source
        for subject_col in source_df.columns:
            if subject_col in target_df.columns:
                # Subject exists - update the column
                if not dry_run:
                    target_df[subject_col] = source_df[subject_col]
                subjects_updated.append(subject_col)
                print(f"  UPDATED: {subject_col}")
            else:
                # New subject - add the column
                if not dry_run:
                    target_df[subject_col] = source_df[subject_col]
                subjects_added.append(subject_col)
                print(f"  ADDED: {subject_col}")
        
        # Sort columns by subject number (S1, S2, S3, etc.)
        def extract_subject_num(col_name):
            """Extract numeric part from subject name like 'S34' -> 34"""
            match = re.match(r'S(\d+)', str(col_name))
            return int(match.group(1)) if match else float('inf')
        
        if not dry_run:
            sorted_columns = sorted(target_df.columns, key=extract_subject_num)
            target_df = target_df[sorted_columns]
        
        # Save the merged data
        if not dry_run:
            # Create backup of original target file
            if target_file.exists():
                backup_path = target_file.with_suffix('.backup' + target_file.suffix)
                shutil.copy2(target_file, backup_path)
                print(f"Backup created: {backup_path}")
            
            # Save merged data in appropriate format
            if target_file.suffix.lower() == '.xlsx':
                # For Excel files, we need to preserve other sheets and write to the correct sheet
                with pd.ExcelWriter(target_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    target_df.to_excel(writer, sheet_name='Compiled_BatchRun', index=True)
            else:
                target_df.to_csv(target_file, index=True)
            print(f"Saved merged data to: {target_file}")
        
        # Summary
        print(f"\nCOMPILED BATCH MERGE SUMMARY:")
        print(f"  Subjects updated: {len(subjects_updated)} - {subjects_updated}")
        print(f"  Subjects added: {len(subjects_added)} - {subjects_added}")
        print(f"  Total subjects in target: {len(target_df.columns)}")
        
        if dry_run:
            print(f"  [DRY RUN - No changes made]")
        
        return True
        
    except Exception as e:
        print(f"Error merging Compiled_BatchRun data: {e}")
        return False


def merge_subject_data(source_file: Path, target_file: Path, dry_run: bool = False, 
                      subject_filter: Optional[str] = None, version: str = "5.0.1") -> bool:
    """
    Main function that merges both Individual_SNR_Power and Compiled_BatchRun data.
    
    This function now handles both file types in the merge step.
    """
    
    # Original Individual_SNR_Power merge logic
    individual_success = merge_individual_snr_data(source_file, target_file, dry_run, subject_filter)
    
    # New Compiled_BatchRun merge logic
    _, batch_name = get_version_file_names(version)
    source_batch_file = source_file.parent / batch_name    
    target_batch_file = target_file.parent / "Compiled_BatchRun_NIH_study.xlsx"
    
    batch_success = merge_compiled_batch_data(source_batch_file, target_batch_file, dry_run)
    
    return individual_success and batch_success


def merge_individual_snr_data(source_file: Path, target_file: Path, dry_run: bool = False, 
                            subject_filter: Optional[str] = None) -> bool:
    """
    Original function for merging Individual_SNR_Power Excel files.
    (Renamed from the original merge_subject_data function)
    """
    # [Keep all the existing Individual_SNR_Power merge logic here]
    # This is the existing code from your merge_subject_data.py
    
    try:
        if not source_file.exists():
            print(f"Source file not found: {source_file}")
            return False
        
        print(f"\n{'='*60}")
        print(f"MERGING INDIVIDUAL SNR DATA")
        print(f"{'='*60}")
        print(f"Source: {source_file}")
        print(f"Target: {target_file}")
        
        # Get subjects from both files
        source_subjects = get_subject_sheets(source_file)
        target_subjects = get_subject_sheets(target_file) if target_file.exists() else {}
        
        print(f"Source subjects: {list(source_subjects.keys())}")
        print(f"Target subjects: {list(target_subjects.keys())}")
        
        # Apply subject filter if provided
        if subject_filter:
            filtered_subjects = {}
            filter_list = subject_filter.split(',')
            for subject_id in source_subjects:
                if subject_id in filter_list:
                    filtered_subjects[subject_id] = source_subjects[subject_id]
            source_subjects = filtered_subjects
            print(f"Filtered to subjects: {list(source_subjects.keys())}")
        
        if not source_subjects:
            print("No subjects found to merge")
            return True
        
        # Create target file if it doesn't exist
        if not target_file.exists():
            print(f"Target file doesn't exist, creating new one: {target_file}")
            if not dry_run:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
            print(f"Created new target file with {len(source_subjects)} subjects")
            return True
        
        # Load workbooks
        source_wb = load_workbook(source_file, data_only=True)
        target_wb = load_workbook(target_file)
        
        subjects_updated = []
        subjects_added = []
        
        # Process each subject
        for subject_id, sheet_names in source_subjects.items():
            if subject_id in target_subjects:
                subjects_updated.append(subject_id)
                action = "UPDATE"
            else:
                subjects_added.append(subject_id)
                action = "ADD"
            
            print(f"\n{action}: {subject_id}")
            
            # Copy all sheets for this subject
            for sheet_name in sheet_names:
                if not dry_run:
                    success = copy_sheet_data(source_wb, target_wb, sheet_name)
                    if not success:
                        print(f"    Failed to copy sheet: {sheet_name}")
                else:
                    print(f"    Would copy sheet: {sheet_name}")
        
        # Save the merged workbook
        if not dry_run:
            # Create backup
            backup_path = target_file.with_suffix('.backup.xlsx')
            shutil.copy2(target_file, backup_path)
            print(f"\nBackup created: {backup_path}")
            
            # Save merged data
            target_wb.save(target_file)
            print(f"Saved merged data to: {target_file}")
        
        # Summary
        print(f"\nINDIVIDUAL SNR MERGE SUMMARY:")
        print(f"  Subjects updated: {len(subjects_updated)} - {subjects_updated}")
        print(f"  Subjects added: {len(subjects_added)} - {subjects_added}")
        
        if dry_run:
            print(f"  [DRY RUN - No changes made]")
        
        return True
        
    except Exception as e:
        print(f"Error merging Individual_SNR data: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Merge subject data from new Individual_SNR output into master file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Use default paths
    python merge_subject_data.py
    
    # Specify custom paths
    python merge_subject_data.py --source "path/to/new/file.xlsx" --target "path/to/master/file.xlsx"
    
    # Preview changes without making them
    python merge_subject_data.py --dry-run
        """
    )
    
    parser.add_argument("--source", "-s",
                       help="Path to source Individual_SNR file (new data)")
    parser.add_argument("--target", "-t", 
                       help="Path to target Individual_SNR file (master)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without making them")
    parser.add_argument("--version", choices=["5.0.1", "4.6", "4.3.1"], 
                   default="5.0.1", help="MATLAB version (determines source file naming)")
    
    args = parser.parse_args()
    
    # Set default paths
    script_dir = Path(__file__).resolve().parent
    
    if args.source:
        source_file = Path(args.source)
    else:
        # Default: look for the newest output in matlab_outputs/version_5.0.1
        individual_name, _ = get_version_file_names(args.version)
        source_file = script_dir / "matlab_outputs" / f"version_{args.version}" / individual_name
        #source_file = default_source
    
    if args.target:
        target_file = Path(args.target)
    else:
        # Default: master file in FinalPythonScripts
        default_target = script_dir / "FinalPythonScripts" / "Individual_SNR_Power_NIH.xlsx"
        target_file = default_target
    
    print(" Subject Data Merger")
    print("=" * 50)
    print(f"Source file: {source_file}")
    print(f"Target file: {target_file}")
    
    if args.dry_run:
        print("Mode: DRY RUN (preview only)")
    else:
        print("Mode: MERGE (will modify files)")
    
    # Validate source file
    if not source_file.exists():
        print(f"\n Source file not found: {source_file}")
        
        # Try to find alternative files
        if source_file.parent.exists():
            alt_files = list(source_file.parent.glob("Individual_SNR*.xlsx"))
            if alt_files:
                print("\n Found alternative files:")
                for f in alt_files:
                    print(f"  - {f.name}")
        
        sys.exit(1)
    
    # Run the merge
    success = merge_subject_data(source_file, target_file, args.dry_run, version=args.version)
    
    if success:
        print("\n Merge completed successfully!")
        if not args.dry_run:
            print(f"📁 Updated file: {target_file}")
    else:
        print("\n Merge failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()