# Known limitations

These are existing behaviors in the source; packaging does not change the analysis calculations.

1. The master accepts `--matlab_version` but does not pass the version to Step 1's launcher. Select the version at the prompt or use the direct launcher with `--version`.
2. The 4.6 MATLAB entry point reads the project-relative `itsVer_4.6/` folder. Passing another directory to Python does not change that MATLAB path.
3. `its_file_renamer.py` (Step -1), `group_average_smooth_plots_no_ema.py` (Step 8), and `Code_Individual_Data_Percentages_SNRs._UPDATED_Each_Day.py` (called by Step 7) were absent from the supplied source. The default full pipeline includes an unavailable step. Use individual supported steps.
4. Step 0 requires recording CSVs in `recording_files/`. Real input data and a validated recording-CSV schema/example were not supplied for public distribution. This package does not invent an end-to-end example.
5. The histogram script uses working-directory-relative paths for some outputs and subprocess calls. Step 7 is not a complete distributed workflow until its missing helper is restored.
6. Versions 4.3.1 and 5.0.1 retain historical machine-specific paths and Excel/COM behavior. The public package does not claim they run on Mac or on an arbitrary Windows setup. Configure and validate them separately. The 5.0.1 script also begins with `clear all`, which may discard wrapper-provided values.
7. The legacy MATLAB command catches errors without rethrowing them; the Python launcher contains fallback/placeholder output creation. A zero exit status or a workbook filename alone does not prove a successful analysis. Inspect the MATLAB console and the actual workbook contents and timestamps.
8. A local copied `xlswrite.m` with a MathWorks copyright notice was excluded from distribution. MATLAB must resolve its installed `xlswrite` function for code that calls it. Legacy spreadsheet behavior may differ and has not been tested after this exclusion. Existing 4.6 paths using `writecell`/`writematrix` are preserved.
9. Exact Python dependency versions and original environment details were not recorded. The dependency list has not been tested through a clean installation. MATLAB and numerical output equivalence were not tested here.
10. The `.gitignore` prevents ordinary addition of matching local files; it does not remove files already committed or prevent a forced add. Review the staged file list before committing.
