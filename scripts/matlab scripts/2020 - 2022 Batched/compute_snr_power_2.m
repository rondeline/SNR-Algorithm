% compute_snr_power_2.m
% Modified from compute_snr.m, so that weighted averages are now based on
% power, not dB.
%  18-Jun-2019
%
% 15-Sep-2019
% New version, to use pause following each conversation

%
% Script file to compute SNR for Female, Male, Other Child, Combined over Male, Female, Other Child, and for Child
% Based on program analyze_its_file.m
% 25-May-2018
% 14-Jun-2018
% 22-Jun-2018 - Updated to compute SNR separately for "Near" and "Far" for
%      each speaker.
% Tharpe, Hornsby, Benitez Project

clear all

global statSTR
global grand_data_block
global Inclusion_Boundaries
global dB_Correction
global LENA_labels

global h1_row h2_row
global h2a_col h2b1_col h2b2_col
global h3_col h3_row
global headings2a

% for counting labels and computing proportional durations

LENA_labels = {'FAN', 'FAF', 'MAN', 'MAF', 'CXN', 'CXF', 'CHN', 'CHF', 'NON', 'NOF', 'TVN', 'TVF', 'OLN', 'OLF', 'SIL'};
number_labels = length(LENA_labels);
statSTR.Label_Count = zeros(number_labels, 2);    % allocate space for counts
statSTR.Label_Duration = zeros(number_labels, 2);  % and for durations

SNR_output_file = [pwd filesep 'soft_speech_SNR_Power_2.xlsx'];

% first prompt for file to analyze:
[filen pathn] = uigetfile('*.txt', 'Select File to Analyze');
fullname = [pathn filesep filen];
fid = fopen(fullname, 'rt');
if fid <= 0
    disp('Sorry, could not open the file.')
    return
end
[~, sheetname] = fileparts(fullname);  % get just filename, without extension, which will become sheet name

% Now, see if output file exists. If not, user may create it
if ~exist(SNR_output_file)
    disp(['Output file ' SNR_output_file ' does not exist.'])
    yn = input('Do you want to create it? [y or n]: ', 's');
    if isempty(yn)  || upper(yn) ~= 'Y'
        disp('OK, exiting...')
        return
    end
    xlswrite(SNR_output_file, NaN);  % create blank file
    
    % delete sheets 2 and 3 from this blank file if they exist, and name
    % remaining sheet according to subject and session
    [~, B] = xlsfinfo(SNR_output_file); % get sheet names
    nsheets = length(B);
    if nsheets > 1
        e = actxserver('Excel.Application'); % delete Sheets 2 & 3
        ewb = e.Workbooks.Open(SNR_output_file);
        for k = 2:nsheets
            ewb.Worksheets.Item(['Sheet' int2str(k)]).Delete;
        end
        ewb.Save
        ewb.Close(false)
    end
    rename_sheet(SNR_output_file, 1, sheetname)
    write_SNR_headings_2(SNR_output_file, 1)
    xlswrite(SNR_output_file, {sheetname}, sheetname, 'A1')  % id at upper left
    bolden(SNR_output_file, 1, {'A1'})   % bolden it
    sheet_no = 1;
else
    sheet_no = new_worksheet_2(SNR_output_file, sheetname);    % create new worksheet (or write over existing one)
end

dB_Correction = 97;   % to convert LINA levels to dBA (?)

number_of_rows_grand = 1000;  % pick a big number
number_of_columns_grand = 60; % pick a large enough number

grand_data_block = num2cell(NaN * ones(number_of_rows_grand, number_of_columns_grand));  % for storage of detailed data

% Get inclusion times associated with this file
% Inclusion_Boundaries = get_inclusion_times(filen);

Inclusion_Boundaries = get_inclusion_times(fullname);
if isscalar(Inclusion_Boundaries)
    disp('Inclusion file read problem! Exiting...')
    return   % problem encountered
end

whole_text = fscanf(fid, '%c');   % read in the whole file as text

% now find the beginning and ending phrases
start_place = strfind(whole_text, 'Flow');
if length(start_place) ~= 1
    disp('Could not find opening phrase in file')
    return
end
stop_place = strfind(whole_text, 'the Bars');
if length(stop_place) ~= 1
    disp('Could not find closing phrase in file.')
    return
end

whole_text = whole_text(start_place:stop_place);  % keep only relevant part

% Get boundaries of conversations
conversation_start = findstr(whole_text, 'Conversation CHF');
conversation_stop = findstr(whole_text, 'Conversation>');
if length(conversation_start) ~= length(conversation_stop)
    disp('Problem with conversation markers!')
    return
end

% pause_start = findstr(whole_text, 'Pause num');
% pause_stop = findstr(whole_text, 'Pause>');
% if length(pause_start) ~= length(pause_stop)
%     disp('Problem with pause markers!')
%     return
% end
% 
% unequal_lengths = false;
% if length(conversation_start) ~= length(pause_start)
%     fprintf('\nWarning! Different number of conversations (%d) and pauses (%d)\n\n', length(conversation_start), length(pause_start));
%     yn = input('Enter Y to continue anyway: ', 's');
%     if upper(yn) ~= 'Y'
%         disp('Exiting...')
%         return
%     end
%     unequal_lengths = true;
% end

% allocate space for chunk stats
number_chunks = length(conversation_start);

statSTR.minimum_time = 0;
statSTR.Noise_Power_Sum = zeros(number_chunks,1);
statSTR.OLN_conv_Power_Sum = zeros(number_chunks,1);  % overlap near and far (conversations)
statSTR.OLF_conv_Power_Sum = zeros(number_chunks,1);
statSTR.OLN_pause_Power_Sum = zeros(number_chunks,1);  % overlap near and far (pausess)
statSTR.OLF_pause_Power_Sum = zeros(number_chunks,1);
statSTR.FAN_Power_Sum = zeros(number_chunks,1);
statSTR.FAF_Power_Sum = zeros(number_chunks,1);
statSTR.MAN_Power_Sum = zeros(number_chunks,1);
statSTR.MAF_Power_Sum = zeros(number_chunks,1);
statSTR.CXN_Power_Sum = zeros(number_chunks,1);
statSTR.CXF_Power_Sum = zeros(number_chunks,1);
statSTR.CHN_Power_Sum = zeros(number_chunks,1);
statSTR.CHF_Power_Sum = zeros(number_chunks,1);
statSTR.ComboN_Power_Sum = zeros(number_chunks,1); % combination of Male, Female, and OtherChild
statSTR.ComboF_Power_Sum = zeros(number_chunks,1); % combination of Male, Female, and OtherChild

statSTR.Noise_Duration = zeros(number_chunks,1);
statSTR.OLN_conv_Duration = zeros(number_chunks,1);  % overlap near and far (conversations)
statSTR.OLF_conv_Duration = zeros(number_chunks,1);
statSTR.OLN_pause_Duration = zeros(number_chunks,1);  % overlap near and far (pausess)
statSTR.OLF_pause_Duration = zeros(number_chunks,1);
statSTR.FAN_Duration = zeros(number_chunks,1);
statSTR.FAF_Duration = zeros(number_chunks,1);
statSTR.MAN_Duration = zeros(number_chunks,1);
statSTR.MAF_Duration = zeros(number_chunks,1);
statSTR.CXN_Duration = zeros(number_chunks,1);
statSTR.CXF_Duration = zeros(number_chunks,1);
statSTR.CHN_Duration = zeros(number_chunks,1);
statSTR.CHF_Duration = zeros(number_chunks,1);
statSTR.ComboN_Duration = zeros(number_chunks,1);
statSTR.ComboF_Duration = zeros(number_chunks,1);

statSTR.Conversation_Start = zeros(number_chunks,1);
statSTR.Conversation_End = zeros(number_chunks,1);
% statSTR.Pause_Start = zeros(number_chunks,1);
% statSTR.Pause_End = zeros(number_chunks,1);

line2rite = 0;
for ipair = 1:number_chunks
    convers_segment = whole_text(conversation_start(ipair):conversation_stop(ipair));  % conversation
    [pause_segment, pause_number] = get_following_pause(whole_text(conversation_stop(ipair):end));                   % pause
    if pause_number == 0   % means a pause was not found
        fprintf('Warning - No pause found for Conversation #%d -- Omitting...\n', ipair);
        continue
    end
    [conv_start_time, conv_end_time, pause_start_time, pause_end_time] = get_chunk_times(convers_segment, pause_segment);
    if conv_end_time ~= pause_start_time
        fprintf('Warning - Pause start time not equal to Conversation end time for Conversation #%d -- Omiting...\n', ipair);
        continue
    end
    if check_inclusion(conv_start_time, conv_end_time)
        line2rite = line2rite + 1;
        process_SNR_Power_2(convers_segment, pause_segment, ipair, pause_number, conv_start_time, conv_end_time, pause_start_time, pause_end_time, line2rite)
    end
end

% compute weighted average levels over all conversations/pauses (for the
% entire day)
datax = compute_weighted_averages_Power; % function to compute weighted averages for day
col_x = h2a_col + length(headings2a) - 5;
rngx = [xlcolumnletter(col_x) int2str(h2_row+1)];
xlswrite(SNR_output_file, datax, sheet_no, rngx)

rng = [xlcolumnletter(h2a_col) int2str(h2_row+3)];
xlswrite(SNR_output_file, grand_data_block, sheet_no, rng)

% write the table of number, actual durations, and proportional durations
% first the numbers
conv_numb = num2cell([statSTR.Label_Count(:,1); NaN; sum(statSTR.Label_Count(:,1))]);
xlswrite(SNR_output_file, conv_numb, sheet_no, [xlcolumnletter(h3_col+1) int2str(h3_row+3)])
pause_numb = num2cell([statSTR.Label_Count(:,2); NaN; sum(statSTR.Label_Count(:,2))]);
xlswrite(SNR_output_file, pause_numb, sheet_no, [xlcolumnletter(h3_col+5) int2str(h3_row+3)])

% next the actual durations
dur_conv = statSTR.Label_Duration(:,1);
dur_conv = round(dur_conv*100)/100;
conv_dur_total = sum(dur_conv);
dur_conv = num2cell([dur_conv; NaN; round(conv_dur_total*100)/100]);
xlswrite(SNR_output_file, dur_conv, sheet_no, [xlcolumnletter(h3_col+2) int2str(h3_row+3)])

dur_pause = statSTR.Label_Duration(:,2);
dur_pause = round(dur_pause*100)/100;
pause_dur_total = sum(dur_pause);
dur_pause = num2cell([dur_pause; NaN; round(pause_dur_total*100)/100]);
xlswrite(SNR_output_file, dur_pause, sheet_no, [xlcolumnletter(h3_col+6) int2str(h3_row+3)])

% next the duration proportions

conv_proportions = statSTR.Label_Duration(:,1)/conv_dur_total;
conv_proportions = round(conv_proportions * 100)/100;   % two decimal places
conv_proportions = num2cell([conv_proportions; NaN; sum(conv_proportions)]);
xlswrite(SNR_output_file, conv_proportions, sheet_no, [xlcolumnletter(h3_col+3) int2str(h3_row+3)])

pause_proportions = statSTR.Label_Duration(:,2)/pause_dur_total;
pause_proportions = round(pause_proportions * 100)/100;   % two decimal places
pause_proportions = num2cell([pause_proportions; NaN; sum(pause_proportions)]);
xlswrite(SNR_output_file, pause_proportions, sheet_no, [xlcolumnletter(h3_col+7) int2str(h3_row+3)])
