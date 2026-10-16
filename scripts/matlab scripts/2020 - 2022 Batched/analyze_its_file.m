% analyze_its_file
% Script file to analyze speech segments in LENA "its" file
% Based on prototype initial program compute_ave_speech.m.
% 5-Dec-2017
%
% Updated May 1, 2018, to include labels 'NON', 'NOF', 'TVN', 'TVF', 'SIL'
%
% Tharpe, Hornsby, Benitez Project

global LENA_labels
global statSTR
global xlsfileSTR
global grand_data_block
global grand_data_block2
global Inclusion_Boundaries

LENA_labels = {'FAN', 'FAF', 'MAN', 'MAF', 'CXN', 'CXF', 'CHN', 'CHF', 'NON', 'NOF', 'TVN', 'TVF', 'SIL'};
number_labels = length(LENA_labels);
statSTR.Power_Sum = zeros(number_labels,2);
statSTR.dB_Sum = zeros(number_labels,2);
statSTR.Duration_Sum = zeros(number_labels,2);
statSTR.Number_Accepted = zeros(number_labels,2);
statSTR.Number_Rejected = zeros(number_labels,2);
statSTR.Duration_Sum = zeros(number_labels,2);
statSTR.minimum_time = 1;    % minimum time segment to consider
statSTR.Number_Utterances = zeros(number_labels,1);   % will be sum of Number_Accepted(:,1) and (:,2) (i.e., both conversations and pauses
statSTR.Number_Utterances_extended = zeros(number_labels,1);  % for "per second" extended array

xlsfileSTR.SheetNames = {'All Segments' 'Level per second', 'Summary Stats'};
xlsfileSTR.start_col3 = 2;   %starting col and row for Sheet  3
xlsfileSTR.start_row3 = 4;

xlsfileSTR.sub_labels = {'Seg#' 'Level' 'Dur' 'type'};
xlsfileSTR.start_col1 = 2;   % for sheet 1
xlsfileSTR.start_row1 = 5;

number_of_rows_grand = 5000;  % pick a big number
number_of_columns_grand = number_labels * (length(xlsfileSTR.sub_labels) + 1);

grand_data_block = num2cell(NaN * ones(number_of_rows_grand, number_of_columns_grand));  % for storage of detailed data
% second data block (extended for multiple rows per utterance) will start
% off with twice as many rows
grand_data_block2 = num2cell(NaN * ones(number_of_rows_grand*2, number_of_columns_grand));  % for storage of detailed data

filen = input('Enter filename to analyze: ', 's');
if ~exist(filen)
    disp('This file could not be found.')
    return
end

fid = fopen(filen, 'rt');
if fid <= 0
    disp('Sorry, could not open the file.')
    return
end

% Get inclusion times associated with this file
Inclusion_Boundaries = get_inclusion_times(filen);
if isscalar(Inclusion_Boundaries)
    disp('Inclusion file read problem! Exiting...')
    return   % problem encountered
end

% open output file and write headers
xlsfileSTR.out_file = write_xls_headers(filen, LENA_labels);

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

% Get boundaries of conversations and pauses, respectively
conversation_start = findstr(whole_text, 'Conversation num');
conversation_stop = findstr(whole_text, 'Conversation>');
if length(conversation_start) ~= length(conversation_stop)
    disp('Problem with conversation markers!')
    return
end


pause_start = findstr(whole_text, 'Pause num');
pause_stop = findstr(whole_text, 'Pause>');
if length(pause_start) ~= length(pause_stop)
    disp('Problem with pause markers!')
    return
end

unequal_lengths = false;
if length(conversation_start) ~= length(pause_start)
    fprintf('\nWarning! Different number of conversations (%d) and pauses (%d)\n\n', length(conversation_start), length(pause_start));
    yn = input('Enter Y to continue anyway: ', 's');
    if upper(yn) ~= 'Y'
        disp('Exiting...')
        return
    end
    unequal_lengths = true;
end

% allocate space for chunk stats
number_chunks = max(length(conversation_start), length(pause_start));
convers_number = zeros(number_chunks,1);
convers_start_time = convers_number;
convers_end_time =  convers_number;
pause_number = convers_number;
pause_start_time = pause_number;
pause_end_time = pause_number;

% Do we need to save the start and end times for each chunk? Maybe not.

% Assume they're alternating
for ipair = 1:min(length(conversation_start), length(pause_start))
    convers_segment = whole_text(conversation_start(ipair):conversation_stop(ipair));
    [convers_number(ipair), convers_start_time(ipair), convers_end_time(ipair), includ_convers] = get_chunk_stats(convers_segment);
    % convers_number(ipair) should be the same as ipair
    pause_segment = whole_text(pause_start(ipair):pause_stop(ipair));
    [pause_number(ipair), pause_start_time(ipair), pause_end_time(ipair), includ_pause] = get_chunk_stats(pause_segment);
    if conversation_start(ipair) < pause_start(ipair)  % determine order
        if includ_convers
            process_chunk(convers_segment, 'c', convers_number(ipair));
        end
        if includ_pause
            process_chunk(pause_segment, 'p', pause_number(ipair));
        end
    else
        if includ_pause
            process_chunk(pause_segment, 'p', pause_number(ipair));
        end
        if includ_convers
            process_chunk(convers_segment, 'c', convers_number(ipair));
        end
    end
end
% if left over chunks:
if unequal_lengths
    if length(conversation_start) > length(pause_start)
        for kseg = length(pause_start)+1 : length(conversation_start)   % extra conversations
            segment = whole_text(conversation_start(kseg):conversation_stop(kseg));
            [convers_number(kseg), convers_start_time(kseg), convers_end_time(kseg), includ_convers] = get_chunk_stats(segment);
            if includ_convers
                process_chunk(segment, 'c', convers_number(kseg))
            end
        end
    else
        for kseg = length(conversation_start)+1 : length(pause_start)   % extra pauses
            segment = whole_text(pause_start(kseg):pause_stop(kseg));
            [pause_number(kseg), pause_start_time(kseg), pause_end_time(kseg), includ_pause] = get_chunk_stats(segment);
            if includ_pause
                process_chunk(segment, 'p', pause_number(kseg))
            end
        end
    end
end
write_block
xlswrite_summary
