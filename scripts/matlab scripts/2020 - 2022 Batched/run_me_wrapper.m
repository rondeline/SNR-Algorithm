function run_me_wrapper(datafolder, compileddataoutput, varargin)
% RUN_ME_WRAPPER  Thin adapter that lets external tools pass
%                 paths into RUNME_Final_ForWindows.m
%
%   run_me_wrapper(DATAFOLDER, COMPILEDDATAOUTPUT)
%   run_me_wrapper(DATAFOLDER, COMPILEDDATAOUTPUT, SUBJECT_FILTER)
%
% Example
%   run_me_wrapper('Z:/LENA/its', ...
%                  'Z:/Results/Compiled_BatchRun.xlsx')
%   run_me_wrapper('Z:/LENA/its', ...
%                  'Z:/Results/Compiled_BatchRun.xlsx', 'S1,S5,S10')

    % Make sure MATLAB's current folder is the one that
    % contains RUNME_Final_ForWindows and its helpers
    cd(fileparts(mfilename('fullpath')));

    % These variables are what RUNME_Final_ForWindows expects
    datafolder         = datafolder;
    compileddataoutput = compileddataoutput;
    
    % Handle optional subject filter
    if nargin >= 3
        subject_filter = varargin{1};
    else
        subject_filter = '';
    end

    % Call the original analysis script
    RUNME_Final_ForWindows
end