function [conv_start_time, conv_end_time, pause_start_time, pause_end_time] = get_chunk_times(convers_segment, pause_segment)
% function [conv_start_time, conv_end_time, pause_start_time, pause_end_time] = get_chunk_times(convers_segment, pause_segment)
% get start time and end time for conversation and pause

x = findstr(convers_segment, 'startTime');  % first get conversation start time
line1 = convers_segment(x(1):end);  % chop off everything prior
y = findstr(line1, '"');
start_time_s = line1(y(1)+1:y(2)-1); % string containing start time
conv_start_time = checkstring(start_time_s);  % check formatting, return numerical value

x = findstr(convers_segment, 'endTime');  % next get end time
line1 = convers_segment(x(1):end);   % chop off everything prior
y = findstr(line1, '"');
end_time_s = line1(y(1)+1:y(2)-1); % string containing end time
conv_end_time = checkstring(end_time_s);  % check formatting

% now for pause
x = findstr(pause_segment, 'startTime');  % get pause start time
line1 = pause_segment(x(1):end);  % chop off everything prior
y = findstr(line1, '"');
start_time_s = line1(y(1)+1:y(2)-1); % string containing start time
pause_start_time = checkstring(start_time_s);  % check formatting, return numerical value

x = findstr(pause_segment, 'endTime');  % next get end time
line1 = pause_segment(x(1):end);   % chop off everything prior
y = findstr(line1, '"');
end_time_s = line1(y(1)+1:y(2)-1); % string containing end time
pause_end_time = checkstring(end_time_s);  % check formatting
