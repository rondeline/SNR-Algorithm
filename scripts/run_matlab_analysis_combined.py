#!/usr/bin/env python3
"""
run_matlab_analysis_combined.py – launch LENA analysis scripts with version selection

This script supports three versions of the LENA analysis:
- Version 5.0.1 (Current): RUNME_Final_ForWindows.m via run_me_wrapper
- Version 4.6: RunME_compute_snr_power_3_FINAL_Marco.m (looks for S1 files)  
- Version 4.3.1: RunME_compute_snr_power_3_FINAL_Marco_4_3_1_Ver.m (looks for S52 files)

Version 5.0.1 uses the wrapper approach and requires --its_dir parameter.
Versions 4.6 and 4.3.1 use hardcoded paths and work in the 2015-2020 Batched directory.

Outputs are automatically organized into version-specific subdirectories:
- matlab_outputs/version_5.0.1/
- matlab_outputs/version_4.6/
- matlab_outputs/version_4.3.1/

Example usage:
    python run_matlab_analysis_combined.py --version 5.0.1 --its_dir "Z:/LENA/its" --output_dir "Z:/Results"
    python run_matlab_analysis_combined.py --version 4.6 --output_dir "Z:/Results"
    python run_matlab_analysis_combined.py --version 4.3.1
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, List
import pandas as pd
import openpyxl
from openpyxl import load_workbook, Workbook
import re
import os
import getpass

# Get current username
USERNAME = getpass.getuser()

#Base directory-
#the folder containing the folder containing the absolute path of this file: os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#take this file-resolveit-go to parent (scripts)-go to parent (noEMA_project)
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Version configurations
# -----------------------------------------------------------------------------

VERSIONS = {
    "5.0.1": {
        "script": "RUNME_Final_ForWindows.m",
        "description": "Version 5.0.1 (Current) - Uses run_me_wrapper with dynamic paths",
        "use_wrapper": True,
        "requires_its_dir": False,
        "default_its_dir": r"Z:\Research Projects\NIH CI study\LENA\RunningCode + Protocol\noEMA_project\its",
        "location": "matlab scripts",
        "output_file": "Compiled_BatchRun.xlsx"
    },
    "4.6": {
        "script": "RunME_compute_snr_power_3_FINAL_Marco.m", 
        "description": "Version 4.6 - Dynamic ITS file processing",
        "use_wrapper": False,
        "requires_its_dir": False,
        "default_its_dir": BASE_DIR / "itsVer_4.6",
        "location": Path("scripts") / "matlab scripts" / "2015 - 2020 Batched",
        "output_file": "Compiled_BatchRun.xlsx"
    },
    "4.3.1": {
        "script": "RunME_compute_snr_power_3_FINAL_Marco_4_3_1_Ver.m",
        "description": "Version 4.3.1 - Dynamic ITS file processing",
        "use_wrapper": False,
        "requires_its_dir": False,
        "default_its_dir": r"Z:\Research Projects\NIH CI study\LENA\RunningCode + Protocol\noEMA_project\itsVer_4.3.1",
        "location": "matlab scripts/2015 - 2020 Batched",
        "base_dir": r"Z:\Research Projects\NIH CI study\LENA\RunningCode + Protocol\noEMA_project\scripts",
        "output_file": "Compiled_BatchRun_Marco2_trial.xlsx"
    }
}

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def quote(path: Path) -> str:
    """Return a MATLAB-safe quoted path (always forward slashes)."""
    return f"'{path.as_posix()}'"


def resolve_its_directory(version: str, its_dir: Optional[str]) -> Path:
    """Resolve the ITS directory for a given version."""
    config = VERSIONS[version]
    
    if its_dir:
        # User provided explicit ITS directory
        its_path = Path(its_dir).resolve()
    elif "default_its_dir" in config:
        # Use version-specific default
        its_path = Path(config["default_its_dir"]).resolve()
    else:
        # Version 5.0.1 or other versions without default
        raise ValueError(f"Version {version} requires --its_dir parameter")
    
    if not its_path.exists():
        raise FileNotFoundError(f"ITS directory not found: {its_path}")
    
    return its_path


def prepare_legacy_data(matlab_dir: Path, its_dir: Path, version: str) -> List[str]:
    """Prepare data files for legacy versions by scanning ITS directory."""
    
    # Scan ITS directory for available subjects
    available_subjects = set()
    its_files = []
    
    for file in its_dir.glob("*.its"):
        # Extract subject from filename (e.g., S10_HH_r1.its -> S10)
        match = re.match(r'(S\d+)', file.name)
        if match:
            subject = match.group(1)
            available_subjects.add(subject)
            its_files.append(file)
    
    print(f"Found {len(available_subjects)} subjects in {its_dir}: {sorted(available_subjects)}")
    
    # Since we modified the MATLAB scripts to have hardcoded paths, 
    # we don't need to create temporary scripts anymore
    return list(available_subjects) 

def prepare_matlab_script_for_subjects(matlab_dir: Path, version: str, subjects: List[str]):
    """Create a modified version of the MATLAB script that processes the found subjects."""
    
    config = VERSIONS[version]
    original_script = matlab_dir / config["script"]
    
    if not original_script.exists():
        raise FileNotFoundError(f"MATLAB script not found: {original_script}")
    
    # Read the original script
    with open(original_script, 'r') as f:
        content = f.read()
    
    # Modify the ID cell array to include all found subjects
    subjects_str = "', '".join(subjects)
    new_id_section = f"ID = {{\n         '{subjects_str}'\n         }};"
    
    # Replace the hardcoded ID section
    # Look for the pattern: ID = { 'S##' };
    id_pattern = r"ID\s*=\s*\{\s*'S\d+'\s*[^}]*\};"
    
    if re.search(id_pattern, content, re.MULTILINE | re.DOTALL):
        modified_content = re.sub(id_pattern, new_id_section, content, flags=re.MULTILINE | re.DOTALL)
        
        # Create a temporary modified script
        temp_script = matlab_dir / f"temp_{config['script']}"
        with open(temp_script, 'w') as f:
            f.write(modified_content)
        
        print(f"Created temporary script with {len(subjects)} subjects: {temp_script.name}")
        return temp_script
    else:
        print(f"Warning: Could not find ID pattern in {original_script}")
        return original_script


def run_matlab_analysis(its_dir: Optional[str], output_dir: Optional[str], 
                       matlab_path: Optional[str], version: Optional[str],
                       subject: Optional[str] = None) -> Optional[Path]:
    """Main function to run the MATLAB analysis with enhanced error handling."""

    # Parse subject input into list
    subject_list = parse_subject_range(subject) if subject else None

    # Validate that specified subjects exist in the its_dir
    if subject_list and its_dir:
        its_path = Path(its_dir)
        available_subjects = set()
        
        # Check what subjects are actually available (check both .its and .txt files)
        for file in its_path.glob("*.its"):
            # Extract subject from filename (e.g., S10_HH_r1.its -> S10)
            match = re.match(r'(S\d+)', file.name)
            if match:
                available_subjects.add(match.group(1))
        
        for file in its_path.glob("*.txt"):
            # Extract subject from filename (e.g., S1_r1.txt -> S1)
            match = re.match(r'(S\d+)', file.name)
            if match:
                available_subjects.add(match.group(1))
        
        # Check if any requested subjects are missing
        missing_subjects = [s for s in subject_list if s not in available_subjects]
        if missing_subjects:
            print(f"Warning: The following subjects were not found in {its_dir}:")
            for missing in missing_subjects:
                print(f"  - {missing}")
            print(f"Available subjects: {sorted(available_subjects)}")
            
            if len(missing_subjects) == len(subject_list):
                print("No valid subjects found. Exiting.")
                return None
            else:
                valid_subjects = [s for s in subject_list if s in available_subjects]
                print(f"Proceeding with valid subjects: {valid_subjects}")
                subject = ','.join(valid_subjects)
    
    script_dir = Path(__file__).resolve().parent
    
    # Version selection
    if not version:
        version = prompt_version_selection()
    elif version not in VERSIONS:
        sys.exit(f"Invalid version: {version}. Available versions: {', '.join(VERSIONS.keys())}")

    config = VERSIONS[version]

    # Resolve ITS directory for all versions now
    try:
        its_path = resolve_its_directory(version, its_dir)
        print(f"Using ITS directory: {its_path}")
    except (ValueError, FileNotFoundError) as e:
        sys.exit(str(e))
    
    # Setup directories based on version
    if config["use_wrapper"]:
        matlab_dir = script_dir / "matlab scripts"
    else:
        matlab_dir = BASE_DIR / config["location"]

    # Check directory exists
    if not matlab_dir.exists():
        sys.exit(f"MATLAB directory not found: {matlab_dir}")

    # Prepare legacy data ONLY for non-wrapper versions
    if not config["use_wrapper"]:
        available_subjects = prepare_legacy_data(matlab_dir, its_path, version)
        if not available_subjects:
            sys.exit(f"No subjects found in ITS directory: {its_path}")

    # Setup output directory with version-specific subfolder
    if config.get("base_dir") and not config.get("use_wrapper"):
        # Use base_dir for legacy versions
        base_output_dir = Path(config["base_dir"]) / "matlab_outputs"
    else:
        # Use provided output_dir or default for wrapper versions
        base_output_dir = Path(output_dir or script_dir / "matlab_outputs").resolve()
        
    output_dir = base_output_dir / f"version_{version}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for required data files (legacy versions only)
    if not config.get("use_wrapper", False):
        has_data = check_data_files(matlab_dir, version)
        if not has_data:
            print(f"\nWarning: No data files found for version {version}")
            print("The analysis may still work if data files are loaded dynamically.")
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response != 'y':
                print("Cancelled by user.")
                return None

    # MATLAB executable
    matlab_exe = Path(matlab_path) if matlab_path else Path("matlab")
    
    # Build MATLAB command based on version
    if config["use_wrapper"]:
        out_xlsx = output_dir / config["output_file"]
        matlab_cmd = build_matlab_cmd_v5(matlab_exe, matlab_dir, its_path, out_xlsx, subject)
    else:
        matlab_cmd = build_matlab_cmd_legacy(matlab_exe, matlab_dir, version, its_path)
    
    # Change working directory before running MATLAB for legacy versions
    original_cwd = Path.cwd()
    if not config.get("use_wrapper", False):
        print(f"Changing working directory to: {matlab_dir}")
        os.chdir(matlab_dir)
    
    try:
        # First try without capturing output to see what happens
        print("\nRunning MATLAB (output will be displayed directly)...")
        result = subprocess.run(matlab_cmd, shell=True, check=True, timeout=600)  # 10 minute timeout
        print("\nMATLAB execution completed successfully.")
            
    except subprocess.TimeoutExpired:
        print("MATLAB execution timed out after 10 minutes")
        return None
    except subprocess.CalledProcessError as err:
        print(f"MATLAB exited with status {err.returncode}")
        print("Continuing to check for partial output files...")
        
    except FileNotFoundError:
        sys.exit("MATLAB executable not found. Please specify --matlab_path or ensure MATLAB is on your PATH.")
    finally:
        # Restore original working directory
        if not config.get("use_wrapper", False):
            os.chdir(original_cwd)

    # Check what files exist in the working directory after MATLAB execution
    print(f"\nPost-execution file check in {matlab_dir}:")
    post_files = list(matlab_dir.glob("*.xlsx"))
    if post_files:
        print("Excel files found after execution:")
        for f in post_files:
            print(f"  {f.name} ({f.stat().st_size} bytes)")
    else:
        print("No Excel files found after execution.")
        '''
    # Also check for any files that might have been created in the ITS directory
    its_excel_files = list(its_path.glob("*.xlsx"))
    if its_excel_files:
        print(f"\nExcel files found in ITS directory {its_path}:")
        for f in its_excel_files:
            print(f"  {f.name} ({f.stat().st_size} bytes)")
            # Move these to the working directory
            dest = matlab_dir / f.name
            if not dest.exists():
                shutil.copy2(f, dest)
                print(f"  Copied to working directory: {f.name}")
    '''

    # Move outputs based on version
    print("\nMoving output files...")
    if config["use_wrapper"]:
        main_output = move_outputs_v5_with_merge(matlab_dir, output_dir, subject)
    else:
        main_output = move_outputs_legacy(matlab_dir, output_dir, version)
    
    if main_output and main_output.exists():
        print(f"\n[SUCCESS] Analysis completed successfully!")
        print(f"Main output file: {main_output}")
        print(f"All outputs saved to: {output_dir}")
    else:
        print(f"\n[WARNING] Analysis completed but output files may be incomplete.")
        print(f"Check the diagnostic report in: {output_dir}")
        print("\nPossible causes:")
        print("1. ITS files don't match expected naming pattern (see debug output above)")
        print("2. ITS files are in wrong format or corrupted")
        print("3. Missing data files that the script expects")
        print("4. MATLAB script encountered silent errors")
        
        # Show what files the script expected vs what was found
    if main_output and main_output.exists():
        print(f"\n[SUCCESS] Analysis completed successfully!")
        print(f"Main output file: {main_output}")
        print(f"All outputs saved to: {output_dir}")
    else:
        print(f"\n[WARNING] Analysis completed but output files may be incomplete.")
        print(f"Check the diagnostic report in: {output_dir}")
        print("\nPossible causes:")
        print("1. ITS files don't match expected naming pattern (see debug output above)")
        print("2. ITS files are in wrong format or corrupted")
        print("3. Missing data files that the script expects")
        print("4. MATLAB script encountered silent errors")
        
        # Show what files the script expected vs what was found
        if version in ["4.6", "4.3.1"]:
            target_subject = "S1" if version == "4.6" else "S52"
            expected_pattern = f"{target_subject}_r*.txt"  # Changed to .txt
            expected_files = list(its_path.glob(expected_pattern))
            print(f"\nExpected files matching '{expected_pattern}': {len(expected_files)}")
            if not expected_files:
                print("This is likely why no output was generated.")
                # Look for both .txt and .its files
                all_txt_files = list(its_path.glob("*.txt"))
                all_its_files = list(its_path.glob("*.its"))
                if all_txt_files:
                    print("Available .txt files:")
                    for f in all_txt_files[:5]:  # Show first 5
                        print(f"  {f.name}")
                    if len(all_txt_files) > 5:
                        print(f"  ... and {len(all_txt_files) - 5} more")
                if all_its_files:
                    print("Available .its files:")
                    for f in all_its_files[:5]:  # Show first 5
                        print(f"  {f.name}")
                    if len(all_its_files) > 5:
                        print(f"  ... and {len(all_its_files) - 5} more")
    
    return main_output


def create_diagnostic_report(matlab_dir: Path, output_dir: Path, version: str):
    """Create a diagnostic report when output files are missing."""
    diagnostic_file = output_dir / f"diagnostic_report_{version}.txt"
    
    with open(diagnostic_file, 'w', encoding='utf-8') as f:
        f.write(f"LENA Analysis Diagnostic Report - Version {version}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Analysis completed but expected output files were not found.\n\n")
        
        f.write(f"Working Directory: {matlab_dir}\n")
        f.write(f"Expected Output: {VERSIONS[version]['output_file']}\n\n")
        
        f.write("Files found in working directory:\n")
        all_files = list(matlab_dir.glob("*"))
        for file in sorted(all_files):
            if file.is_file():
                f.write(f"  {file.name} ({file.stat().st_size} bytes)\n")
            else:
                f.write(f"  {file.name}/ (directory)\n")
        
        f.write("\nPossible issues:\n")
        f.write("1. Missing MATLAB function files (see required functions below)\n")
        f.write("2. Data file format issues - check if ITS files are in correct format\n")
        f.write("3. MATLAB path or permission issues\n")
        f.write("4. Script expecting specific data file patterns\n")
        f.write("5. Script errors not being captured properly\n\n")
        
        f.write("Required MATLAB functions for this version:\n")
        required_functions = [
            "get_inclusion_times.m",
            "get_following_pause.m", 
            "get_chunk_times.m",
            "check_inclusion.m",
            "compute_weighted_averages_Power.m",
            "new_worksheet_deleteallcontent.m",
            "bolden.m",
            "rename_sheet.m",
            "Header_Maker.m",
            "process_line3.m" if version == "4.6" else "process_line3_4_3_1.m"
        ]
        
        for func in required_functions:
            func_path = matlab_dir / func
            status = "[FOUND]" if func_path.exists() else "[MISSING]"
            f.write(f"  {func} - {status}\n")
    
    print(f"Created diagnostic report: {diagnostic_file}")

def create_placeholder_output(output_dir: Path, filename: str, version: str):
    """Create a placeholder Excel file with basic structure when analysis fails."""
    try:
        from openpyxl import Workbook
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Analysis_Failed"
        
        # Add headers explaining the situation
        ws['A1'] = f"LENA Analysis Version {version} - Output File Creation Failed"
        ws['A2'] = "This placeholder file was created because the MATLAB analysis did not produce output files."
        ws['A3'] = "Please check the diagnostic report for more information."
        ws['A4'] = f"Expected output: {filename}"
        ws['A5'] = f"Generated on: {Path.cwd()}"
        
        # Add some basic structure that might be expected
        ws['A7'] = "Subjects"
        ws['A8'] = "No data available - analysis failed"
        
        output_file = output_dir / filename
        wb.save(output_file)
        print(f"Created placeholder output file: {output_file}")
        
    except Exception as e:
        print(f"Could not create placeholder file: {e}")

def prompt_version_selection() -> str:
    """Prompt user to select which version to use."""
    print("\nAvailable LENA Analysis Versions:")
    print("=" * 60)
    
    for version, config in VERSIONS.items():
        print(f"{version}: {config['description']}")
    
    print("\nWhich version would you like to use?")
    
    while True:
        choice = input(f"Enter version ({'/'.join(VERSIONS.keys())}): ").strip()
        
        if choice in VERSIONS:
            print(f"\nSelected: Version {choice}")
            return choice
        else:
            print(f"Invalid choice. Please enter one of: {', '.join(VERSIONS.keys())}")


def check_data_files(matlab_dir: Path, version: str) -> bool:
    """Check if the required MATLAB files exist for legacy versions."""
    config = VERSIONS[version]
    
    # Version 5.0.1 doesn't need this check since it uses dynamic paths
    if config.get("use_wrapper", False):
        return True
    
    # Check if the MATLAB script file exists
    script_path = matlab_dir / config["script"]
    if not script_path.exists():
        print(f"ERROR: MATLAB script not found: {script_path}")
        print(f"Available .m files in {matlab_dir}:")
        m_files = list(matlab_dir.glob("*.m"))
        for f in m_files[:10]:
            print(f"  {f.name}")
        return False
    else:
        print(f" Main script found: {script_path.name}")
    
    # Check for required function files (version-specific)
    required_functions = [
        "get_inclusion_times.m",
        "get_following_pause.m", 
        "get_chunk_times.m",
        "check_inclusion.m",
        "bolden.m",
        "rename_sheet.m",
        "Header_Maker.m"
    ]
    
    # Add version-specific functions
    if version == "4.3.1":
        required_functions.extend([
            "new_worksheet_deleteallcontent_4_3_1.m",
            "process_line3_4_3_1.m",
            "compute_weighted_averages_Power_4_3_1.m"
        ])
    else:  # version 4.6
        required_functions.extend([
            "new_worksheet_deleteallcontent.m",
            "process_line3.m", 
            "compute_weighted_averages_Power.m"
        ])
    
    missing_functions = []
    for func in required_functions:
        func_path = matlab_dir / func
        if not func_path.exists():
            missing_functions.append(func)
    
    if missing_functions:
        print(f"⚠ WARNING: Missing required MATLAB functions:")
        for func in missing_functions:
            print(f"  ✗ {func}")
        print("The analysis may fail without these functions.")
        return False
    
    print(f" All required MATLAB functions found")
    return True


def build_matlab_cmd_v5(matlab_exe: Path, matlab_dir: Path, its_dir: Path, out_xlsx: Path, subject_filter: Optional[str] = None) -> str:
    """Build MATLAB command for Version 5.0.1 (uses wrapper)."""
    # genpath => recursively adds every sub-folder of matlab_dir
    if subject_filter:
        matlab_stmt = (
            f"addpath(genpath({quote(matlab_dir)})); "
            f"run_me_wrapper({quote(its_dir)}, {quote(out_xlsx)}, '{subject_filter}');"
        )
    else:
        matlab_stmt = (
            f"addpath(genpath({quote(matlab_dir)})); "
            f"run_me_wrapper({quote(its_dir)}, {quote(out_xlsx)});"
        )

    if platform.system() == "Windows":
        return f'"{matlab_exe}" -wait -nosplash -nodesktop -r "{matlab_stmt} exit"'
    else:
        return f'"{matlab_exe}" -nosplash -nodesktop -batch "{matlab_stmt}"'



def build_matlab_cmd_legacy(matlab_exe: Path, matlab_dir: Path, version: str, its_dir: Path) -> str:
    """Build MATLAB command for legacy versions - direct script execution with better error handling."""
    config = VERSIONS[version]
    
    # Use the temporary script if it was created, otherwise use the original
    temp_script = matlab_dir / f"temp_{config['script']}"
    if temp_script.exists():
        script_name_no_ext = temp_script.stem
    else:
        script_name_no_ext = Path(config["script"]).stem
    
    # Enhanced MATLAB command with better error handling and debugging
    matlab_stmt = (
        f"try; "
        f"addpath(genpath('{matlab_dir.as_posix()}')); "
        f"cd('{matlab_dir.as_posix()}'); "
        f"fprintf('\\n=== MATLAB Debug Info ===\\n'); "
        f"fprintf('MATLAB Version: %s\\n', version); "
        f"fprintf('Working directory: %s\\n', pwd); "
        f"fprintf('Script to run: {script_name_no_ext}\\n'); "
        f"fprintf('Starting analysis...\\n'); "
        f"tic; "
        f"{script_name_no_ext}; "
        f"elapsed_time = toc; "
        f"fprintf('\\n=== Analysis completed successfully in %.2f seconds ===\\n', elapsed_time); "
        f"catch ME; "
        f"fprintf('\\n=== ERROR OCCURRED ===\\n'); "
        f"fprintf('Error message: %s\\n', ME.message); "
        f"fprintf('Error identifier: %s\\n', ME.identifier); "
        f"if ~isempty(ME.stack); "
        f"fprintf('Error in file: %s\\n', ME.stack(1).file); "
        f"fprintf('Error at line: %d\\n', ME.stack(1).line); "
        f"end; "
        f"fprintf('=== END ERROR INFO ===\\n'); "
        f"end"
    )

    if platform.system() == "Windows":
        return f'"{matlab_exe}" -wait -nosplash -nodesktop -r "{matlab_stmt}; pause(2); exit"'
    else:
        return f'"{matlab_exe}" -nosplash -nodesktop -batch "{matlab_stmt}"'

def move_outputs_v5(matlab_dir: Path, output_dir: Path) -> Optional[Path]:
    """Move outputs for Version 5.0.1."""
    # Version 5.0.1 outputs are created in the "2020 - 2022 Batched" subdirectory
    
    # Move any CSV files from the batch directory
    csv_count = 0
    for f in matlab_dir.glob("*.csv"):
        dest = output_dir / f.name
        if dest.exists():
            dest.unlink()
        shutil.move(f, dest)
        csv_count += 1
        print(f"Moved: {f.name}")
    
    # Move Excel output files - look for various Compiled_BatchRun patterns
    xlsx_count = 0
    output_patterns = ["Compiled_BatchRun*.xlsx", "Individual_SNR*.xlsx"]
    
    for pattern in output_patterns:
        for f in matlab_dir.glob(pattern):
            dest = output_dir / f.name
            if dest.exists():
                dest.unlink()
            shutil.move(f, dest)
            xlsx_count += 1
            print(f"Moved: {f.name}")
    
    # Look for the main compilation file
    compiled_files = list(output_dir.glob("Compiled_BatchRun*.xlsx"))
    if compiled_files:
        main_output = compiled_files[0]  # Use the first one found
        print(f"Main output file: {main_output.name}")
    else:
        print(f"Warning: No Compiled_BatchRun*.xlsx files found in {output_dir}")
        # List what files are actually in the directories for debugging
        print(f"Files in batch_dir: {[f.name for f in batch_dir.glob('*.xlsx')]}")
        print(f"Files in output_dir: {[f.name for f in output_dir.glob('*.xlsx')]}")
        return None
    
    print(f"Moved {csv_count} CSV file(s) and {xlsx_count} Excel file(s)")
    return main_output



def move_outputs_legacy(matlab_dir: Path, output_dir: Path, version: str) -> Optional[Path]:
    """Move outputs for legacy versions with enhanced debugging and fallback creation."""
    expected_output = VERSIONS[version]["output_file"]
    
    print(f"\nDebugging output file creation:")
    print(f"Working directory: {matlab_dir}")
    print(f"Expected output file: {expected_output}")
    
    # List all files in the working directory for debugging
    print(f"Files in working directory:")
    all_files = list(matlab_dir.glob("*"))
    xlsx_files = [f for f in all_files if f.suffix.lower() == '.xlsx']
    csv_files = [f for f in all_files if f.suffix.lower() == '.csv']
    
    print(f"  Excel files ({len(xlsx_files)}):")
    for f in xlsx_files:
        print(f"    {f.name} ({f.stat().st_size} bytes)")
    
    print(f"  CSV files ({len(csv_files)}):")
    for f in csv_files:
        print(f"    {f.name} ({f.stat().st_size} bytes)")
    
    # Move any CSV files
    csv_count = 0
    for f in matlab_dir.glob("*.csv"):
        dest = output_dir / f.name
        if dest.exists():
            dest.unlink()
        shutil.move(f, dest)
        csv_count += 1
        print(f"Moved CSV: {f.name}")
    
    # Move Excel output files (look for compilation and individual results)
    xlsx_count = 0
    output_patterns = ["Compiled_*.xlsx", "Individual_*.xlsx", "*.xlsx"]
    
    for pattern in output_patterns:
        for f in matlab_dir.glob(pattern):
            # Skip temporary files
            if f.name.startswith('~'):
                continue
            dest = output_dir / f.name
            if dest.exists():
                dest.unlink()
            shutil.move(f, dest)
            xlsx_count += 1
            print(f"Moved Excel: {f.name}")
    
    # Check for the main output file
    main_output = output_dir / expected_output
    if not main_output.exists():
        # Look for any compilation file
        compiled_files = list(output_dir.glob("Compiled_*.xlsx"))
        if compiled_files:
            main_output = compiled_files[0]
            print(f"Using {main_output.name} as main output file")
        else:
            print(f"Warning: Expected output file {expected_output} not found")
            
            # Create a diagnostic report about what went wrong
            create_diagnostic_report(matlab_dir, output_dir, version)
            
            # As a last resort, create a minimal output file structure
            if csv_count == 0 and xlsx_count == 0:
                print("No output files were created. Creating diagnostic placeholder...")
                create_placeholder_output(output_dir, expected_output, version)
                main_output = output_dir / expected_output
            else:
                print(f"Some files were moved ({csv_count} CSV, {xlsx_count} Excel) but main output missing.")
                return None
    
    print(f"Moved {csv_count} CSV file(s) and {xlsx_count} Excel file(s)")
    return main_output


import pandas as pd
import openpyxl
from openpyxl import load_workbook, Workbook
import shutil
from pathlib import Path
from typing import Optional, List

def get_subjects_from_compiled_file(file_path: Path) -> List[str]:
    """Extract subjects from Compiled_BatchRun file's second sheet."""
    if not file_path.exists():
        return []
    
    try:
        # Read the second sheet (Compiled_BatchRun)
        df = pd.read_excel(file_path, sheet_name=1, nrows=1)  # Just read first row
        # Subjects are in the columns starting from B1
        subjects = [col for col in df.columns if col.startswith('S') and '_' not in str(col)]
        return subjects
    except Exception as e:
        print(f"Warning: Could not read subjects from {file_path}: {e}")
        return []

def get_subjects_from_individual_snr(file_path: Path) -> List[str]:
    """Extract subjects from Individual_SNR file by checking sheet names."""
    if not file_path.exists():
        return []
    
    try:
        xl_file = pd.ExcelFile(file_path)
        sheet_names = xl_file.sheet_names
        # Extract unique subjects from sheet names like "S22_r1"
        subjects = set()
        for sheet in sheet_names:
            if sheet.startswith('S') and '_' in sheet:
                # Extract subject ID (e.g., S22 from S22_r1)
                subject = sheet.split('_')[0]
                subjects.add(subject)
        return list(subjects)
    except Exception as e:
        print(f"Warning: Could not read subjects from {file_path}: {e}")
        return []

def filter_subject_data(source_file: Path, target_file: Path, subject_filter: Optional[str] = None):
    """Handle subject-specific data merging for Individual_SNR file."""
    if not source_file.exists():
        print(f"Source file not found: {source_file}")
        return
    
    # Load source workbook
    wb_source = load_workbook(source_file)
    
    # If target doesn't exist, just copy everything
    if not target_file.exists():
        shutil.copy2(source_file, target_file)
        print(f"Created new file: {target_file}")
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
        
        # Copy all cells
        for row in source_sheet.iter_rows():
            for cell in row:
                target_sheet[cell.coordinate].value = cell.value
                if cell.has_style:
                    target_sheet[cell.coordinate]._style = cell._style
    
    # Save the target workbook
    wb_target.save(target_file)
    wb_source.close()
    wb_target.close()
    print(f"Updated: {target_file}")

def merge_compiled_data(source_file: Path, target_file: Path, subject_filter: Optional[str] = None):
    """Handle subject-specific data merging for Compiled_BatchRun file."""
    if not source_file.exists():
        print(f"Source file not found: {source_file}")
        return
    
    # If target doesn't exist, just copy
    if not target_file.exists():
        shutil.copy2(source_file, target_file)
        print(f"Created new file: {target_file}")
        return
    
    try:
        # Read both files
        source_sheets = pd.read_excel(source_file, sheet_name=None)
        target_sheets = pd.read_excel(target_file, sheet_name=None)
        
        # Get the data sheet (usually second sheet or 'Compiled_BatchRun')
        data_sheet_name = list(source_sheets.keys())[1] if len(source_sheets) > 1 else list(source_sheets.keys())[0]
        
        if data_sheet_name not in target_sheets:
            # Just copy the whole file if structure is different
            shutil.copy2(source_file, target_file)
            print(f"Replaced entire file: {target_file}")
            return
        
        source_df = source_sheets[data_sheet_name]
        target_df = target_sheets[data_sheet_name]
        
        # Get subjects from source
        source_subjects = [col for col in source_df.columns if col.startswith('S') and len(col) <= 4]
        
        if subject_filter:
            # Only process the specified subject
            source_subjects = [s for s in source_subjects if s == subject_filter]
        
        # Update or add subject columns
        for subject in source_subjects:
            if subject in source_df.columns:
                target_df[subject] = source_df[subject]
                print(f"  Updated data for subject: {subject}")
        
        # Write back to Excel
        with pd.ExcelWriter(target_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            target_df.to_excel(writer, sheet_name=data_sheet_name, index=False)
        
        print(f"Updated: {target_file}")
        
    except Exception as e:
        print(f"Error merging compiled data: {e}")
        # Fallback to simple copy
        shutil.copy2(source_file, target_file)
        print(f"Replaced entire file due to error: {target_file}")

def move_outputs_v5_with_merge(matlab_dir: Path, output_dir: Path, subject_filter: Optional[str] = None) -> Optional[Path]:
    """Enhanced version of move_outputs_v5 that handles subject-specific merging."""
    
    # The actual save location
    actual_save_dir = matlab_dir / "2020 - 2022 Batched"
    
    # Check both the matlab_dir and the actual save directory
    search_dirs = [matlab_dir, actual_save_dir] if actual_save_dir.exists() else [matlab_dir]
    
    moved_files = []
    
    # Handle the two special files with merging
    special_files = {
        "Compiled_BatchRun_NIH_study_S14.xlsx": merge_compiled_data,
        "Individual_SNR_Power_NIH_s16.xlsx": filter_subject_data
    }
    
    for pattern, merge_func in special_files.items():
        for search_dir in search_dirs:
            # Look for exact match or pattern
            matching_files = list(search_dir.glob(pattern))
            if not matching_files:
                # Try without extensions or slight variations
                base_pattern = pattern.replace(".xlsx", "*.xlsx")
                matching_files = list(search_dir.glob(base_pattern))
            
            for source_file in matching_files:
                target_file = output_dir / pattern
                print(f"\nProcessing {source_file.name}...")
                
                if subject_filter:
                    print(f"Filtering for subjects: {', '.join(subject_filter)}")
                    # Process each subject in the list
                    for subject in subject_filter:
                        merge_func(source_file, target_file, subject)
                else:
                    # Use the appropriate merge function
                    merge_func(source_file, target_file, None)
                
                moved_files.append(target_file)
                
                # Remove source file after successful merge
                try:
                    source_file.unlink()
                except Exception as e:
                    print(f"Warning: Could not remove source file: {e}")
    
    # Move other files (CSV and other Excel files) normally
    for search_dir in search_dirs:
        # Move CSV files
        for f in search_dir.glob("*.csv"):
            dest = output_dir / f.name
            if dest.exists():
                dest.unlink()
            shutil.move(str(f), str(dest))
            moved_files.append(dest)
            print(f"Moved: {f.name}")
        
        # Move other Excel files (not the special ones)
        for f in search_dir.glob("*.xlsx"):
            if f.name not in special_files:
                dest = output_dir / f.name
                if dest.exists():
                    dest.unlink()
                shutil.move(str(f), str(dest))
                moved_files.append(dest)
                print(f"Moved: {f.name}")
    
    # Find the main output file
    main_output = output_dir / "Compiled_BatchRun.xlsx"
    if main_output.exists():
        return main_output
    else:
        # Look for any compilation file
        compiled_files = list(output_dir.glob("Compiled_*.xlsx"))
        if compiled_files:
            return compiled_files[0]
    
    return None if not moved_files else moved_files[0]

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


# -----------------------------------------------------------------------------
# Main driver
# -----------------------------------------------------------------------------



# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run LENA SNR MATLAB analysis with version selection.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available versions:
  5.0.1   - Current version using RUNME_Final_ForWindows.m via run_me_wrapper (requires --its_dir)
  4.6     - Legacy version for subject S1 (looks for S1_r1.its, S1_r2.its, etc.)
  4.3.1   - Legacy version for subject S52 (looks for S52_XX_Day1.its, S52_XX_Day2.its, etc.)

Version 5.0.1 uses dynamic paths and requires the --its_dir parameter.
Legacy versions (4.6, 4.3.1) use hardcoded paths and work in the '2015-2020 Batched' directory.

Examples:
  # Version 5.0.1 (Current) - requires ITS directory
  python run_matlab_analysis_combined.py --version 5.0.1 --its_dir "Z:/LENA/its" --output_dir "Z:/Results"
  
  # Version 4.6 - legacy version
  python run_matlab_analysis_combined.py --version 4.6 --output_dir "Z:/Results"
  
  # Version 4.3.1 - legacy version
  python run_matlab_analysis_combined.py --version 4.3.1
  
  # Interactive mode (will prompt for version)
  python run_matlab_analysis_combined.py --output_dir "C:/Results"
        """
    )
    
    parser.add_argument("--version", choices=list(VERSIONS.keys()),
                       help="LENA version to use (if not specified, user will be prompted)")
    parser.add_argument("--its_dir",
                   help="Folder containing *.its files. For version 5.0.1, this is required. "
                        "For versions 4.6 and 4.3.1, defaults to version-specific directories: "
                        "itsVer_4.6 and itsVer_4.3.1 respectively.")
    parser.add_argument("--output_dir",
                       help="Base destination folder for results (defaults to ./matlab_outputs). Version-specific subdirectories will be created automatically.")
    parser.add_argument("--matlab_path",
                       help="Full path to MATLAB executable if not on PATH")
    #parser.add_argument("--subj", "-s",
    #                help="Process only a specific subject (e.g., S13, S9)")
    parser.add_argument("--subject", "-s",
                   help="Process specific subject(s). Examples: 'S1', 'S1,S5,S10', 'S1-S5', 'S1-S3,S10,S15-S17'")
    
    args = parser.parse_args()
    
    try:
        run_matlab_analysis(args.its_dir, args.output_dir, args.matlab_path, args.version, args.subject)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)