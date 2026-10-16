function process_chunk(segment, seg_type, chunk_number)
% function process_chunk(segment, seg_type, chunk_number)
% function to process a chunk (either a conversation or a pause)
% Invoked from analyze_its_file

global LENA_labels
global statSTR

minimum_time = statSTR.minimum_time;

number_labels = length(LENA_labels);

if strcmp(upper(seg_type), 'C')
    iord = 1;
else
    iord = 2;
end

% Get each utterance
utter_start = findstr(segment, 'spkr=');
utter_stop = findstr(segment, '/>');
if length(utter_start) ~= length(utter_stop)
    disp ('Problem with utterance delimiters!')
    return
end

for k = 1:length(utter_start)
    utterance = segment(utter_start(k):utter_stop(k));
    label = utterance(7:9);   % here's the label
    indx = find(ismember(LENA_labels, label));
    if ~isempty(indx)
        [start_time, stop_time, level] = process_line2(utterance);
        if check_inclusion(start_time, stop_time)  % process only if times are in range
            
            dur = stop_time - start_time;
            if dur >= minimum_time
                statSTR.Duration_Sum(indx,iord) = statSTR.Duration_Sum(indx,iord) + dur;
                Power = 10.^(level/10) * dur;
                statSTR.Power_Sum(indx,iord) = statSTR.Power_Sum(indx,iord) + Power; % accumulate weighted power
                statSTR.dB_Sum(indx,iord) = statSTR.dB_Sum(indx,iord) + level * dur;
                statSTR.Number_Accepted(indx,iord) = statSTR.Number_Accepted(indx,iord) + 1;
                statSTR.Number_Utterances(indx) = statSTR.Number_Utterances(indx) + 1;     % keep track of segment #, whether conversation or pause
                store_line(indx, level, dur, iord, chunk_number);    % write line to grand arrays
            else
                statSTR.Number_Rejected(indx, iord) = statSTR.Number_Rejected(indx, iord) + 1;
            end
        end
    end
end
