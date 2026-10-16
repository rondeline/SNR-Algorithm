# noEMA LENA analysis pipeline

Python and MATLAB scripts for processing LENA ITS recordings, generating segment workbooks, calculating sound levels and signal-to-noise ratios (SNR), merging results, and producing plots without EMA activity files.

This repository contains source code and input instructions. Recording data, participant metadata, results, historical scripts, and local workbooks are excluded. Add your own inputs locally.

## Requirements and setup

- Python 3.9 or later is a source-syntax baseline, not a tested compatibility guarantee. Use a maintained Python release supported by the installed dependencies.
- MATLAB for Step 1. Version 4.6 is the Windows/Mac analysis branch reported working by the maintainer, including a Mac command using MATLAB R2025a. A full integration test has not been run for this distribution.
- Optional static Plotly PNG export uses `kaleido`, installed separately if needed.

Create and activate a Python environment from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, create the environment with `python -m venv .venv` and activate with `.venv\Scripts\activate.bat` in Command Prompt or `.venv\Scripts\Activate.ps1` in PowerShell.

The version selectors `4.6`, `4.3.1`, and `5.0.1` refer to the LENA analysis code. They are separate from MATLAB release names such as `R2025a`.

## Step 1: run version 4.6

1. Place recording inputs and required segment workbooks in `itsVer_4.6/`. Use the existing recording naming convention, such as `S1_r1.its` and its corresponding segment workbook. Supply each recording once; the script scans both `.its` and `.txt` files.
2. Open a terminal at the repository root, which contains `scripts/` and `itsVer_4.6/`.
3. Run the master pipeline on Mac:

```bash
python scripts/master_lena_pipeline_no_ema.py \
  --steps 1 \
  --matlab_version 4.6 \
  --its_dir ./itsVer_4.6 \
  --matlab-path /Applications/MATLAB_R2025a.app/bin/matlab
```

Select **4.6** when prompted. The existing master accepts `--matlab_version` but does not pass it to the Step 1 launcher. This release preserves that behavior.

Windows example (one line; adjust the installed MATLAB path):

```text
python scripts/master_lena_pipeline_no_ema.py --steps 1 --matlab_version 4.6 --its_dir ./itsVer_4.6 --matlab-path "C:/Program Files/MATLAB/R2025a/bin/matlab.exe"
```

To select 4.6 directly without the version prompt, use the existing launcher:

```bash
python scripts/run_matlab_analysis_combined.py \
  --version 4.6 \
  --its_dir ./itsVer_4.6 \
  --output_dir ./matlab_outputs \
  --matlab_path /Applications/MATLAB_R2025a.app/bin/matlab
```

The master uses `--matlab-path`; the launcher uses `--matlab_path`.

The 4.6 MATLAB script resolves `itsVer_4.6/` relative to its source location, regardless of a different Python `--its_dir` value. Keep the folder structure intact. It scans the top level for `S*_r*.its` and `S*_r*.txt`, not nested directories. The Python launcher collects outputs into `matlab_outputs/version_4.6/` for these commands. MATLAB initially writes working files in its source directory.

## Pipeline steps

Run individual steps from the repository root rather than starting the default whole pipeline. See [known limitations](docs/KNOWN_LIMITATIONS.md).

| Step | Purpose | Command / prerequisites |
| --- | --- | --- |
| 0 | Generate segment workbooks | `python scripts/master_lena_pipeline_no_ema.py --steps 0 --its_dir ./itsVer_4.6 --subjects S1`; requires recording CSVs in `recording_files/` |
| 1 | Calculate SNR in MATLAB | Use a Step 1 command above; no subject filter for the documented 4.6 workflow |
| 2 | Merge results into local masters | `python scripts/master_lena_pipeline_no_ema.py --steps 2 --matlab_version 4.6 --output_dir ./matlab_outputs` |
| 3 | Generate scatter plots | `python scripts/master_lena_pipeline_no_ema.py --steps 3` |
| 6 | Generate smoothed plots | `python scripts/master_lena_pipeline_no_ema.py --steps 6`; consumes Step 3 output |
| 7 | Generate histograms / percentages | Requires local subject information and the missing Each_Day helper described in the limitations; not a complete distributed workflow |

Step 2 reads the versioned MATLAB output workbooks and uses the merge helper to create or update both `Individual_SNR_Power_NIH.xlsx` and `Compiled_BatchRun_NIH_study.xlsx` under `scripts/FinalPythonScripts/`. Do not create blank output workbooks as substitutes for a successful MATLAB run. Step 3 reads the individual master; Steps 3 and 6 write under `outputs/`.

For subject information, see [templates/README.md](templates/README.md). No participant rows are included. The metadata template alone does not resolve Step 7's missing helper.

## MATLAB entry points

| Analysis version | Entry point | Folder under `scripts/matlab scripts/` |
| --- | --- | --- |
| 4.6 | `RunME_compute_snr_power_3_FINAL_Marco.m` | `2015 - 2020 Batched/` |
| 4.3.1 | `RunME_compute_snr_power_3_FINAL_Marco_4_3_1_Ver.m` | `2015 - 2020 Batched/` |
| 5.0.1 | `run_me_wrapper.m` calls `RUNME_Final_ForWindows.m` | `2020 - 2022 Batched/` |

The `FINAL_Marco` name identifies the current 4.6 entry point. The entry names and helper locations have been preserved. Versions 4.3.1 and 5.0.1 are retained as legacy branches without a new Windows/Mac compatibility claim. Their existing machine-specific paths and Excel dependencies require review before use. Do not add the entire repository recursively to MATLAB's path; use the provided launchers.

## Repository contents

- `scripts/`: Python pipeline and MATLAB analysis source.
- `its/`, `itsVer_4.6/`, `itsVer_4.3.1/`, `recording_files/`: local-input folders containing instructions only.
- `matlab_outputs/`, `outputs/`: output-folder instructions only.
- `templates/`: header-only subject-information CSV and instructions.
- `tools/create_subject_info_template.py`: creates a local, empty metadata workbook without overwriting an existing one.
- `requirements.txt`: direct Python dependencies, without invented version pins.
- `.gitignore`: excludes local research inputs, workbooks, outputs, backups, and environments.

## Attribution and licensing

Original author comments and source references are preserved. See [NOTICE.md](NOTICE.md) for the distribution changes and the excluded bundled MathWorks implementation. No repository-wide license was supplied or assigned by this packaging pass. The maintainer should choose an appropriate license after confirming the original code's provenance and permissions.

## Validation

Retained pipeline source files were compared byte-for-byte with the cleaned working copy. Python syntax, command-line help for the master, Git ignore behavior, empty-template creation, and a synthetic merge into newly created master workbooks were checked. MATLAB execution, fresh dependency installation, plotting integration, and numerical equivalence were not tested. See [known limitations](docs/KNOWN_LIMITATIONS.md) before interpreting a completed launcher process as a successful analysis.
