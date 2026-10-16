function [start_time, end_time, level] = process_line2(text_line)
% function [dur, level] = process_line2(text_line)
% function called from analyze_its_file to read a line from
% the LENA .its file and return the start&stop times and average level.
% Similar to process_line1.m
% Dec. 7, 2017.
%
% First extract level

x = findstr(text_line, 'average_dB');  % position of keyword
line1 = text_line(x:end);   % string starting with this keyword
y = findstr(line1, '"');   % position within this string of " marks

level = str2double(line1(y(1)+1:y(2)-1));  % 1st two " marks delimit the value

% now get the duration
x = findstr(text_line, 'startTime');  % first get start time
line1 = text_line(x:end);  % chop off everything prior to keyword
y = findstr(line1, '"');   % delimiters
start_time_s = line1(y(1)+1:y(2)-1); % string containing start time
start_time = checkstring(start_time_s);  % check formatting, return numerical value

x = findstr(text_line, 'endTime');  % next get end time
line1 = text_line(x:end);   % chop off everything prior
y = findstr(line1, '"');
end_time_s = line1(y(1)+1:y(2)-1); % string containing end time
end_time = checkstring(end_time_s);  % check formatting


function time_val = checkstring(time_str)
% function to check format of string time_str.
% If it's valid, return the double value
if time_str(1:2) ~= 'PT'
    disp(['PT not found at start of string (' time_val ')'])
    time_val = 0;
    return
end
if time_str(end) ~= 'S'
    disp(['S not found at end of string (' time_val ')'])
    return
end

time_val = str2double(time_str(3:end-1));

