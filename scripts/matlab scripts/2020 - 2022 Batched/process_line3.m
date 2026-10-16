function [start_time, end_time, level] = process_line3(text_line)
% function [dur, level] = process_line3(text_line)
% function called from compute_snr.m to read a line from
% the LENA .its file and return the start&stop times and average level.
% Similar to process_line1.m
% Dec. 7, 2017.
% This version (process_line3.m) incorporates linear modification for
% levels below 50 dB, to adjust for the expansion that the LENA device
% applies for these levels. 12-July-2018.
%
% First extract level

global dB_Correction

cutoff = 30;   % levels below this need to be adjusted
slope = 0.4;

x = findstr(text_line, 'average_dB');  % position of keyword
line1 = text_line(x:end);   % string starting with this keyword
y = findstr(line1, '"');   % position within this string of " marks

level = str2double(line1(y(1)+1:y(2)-1));  % 1st two " marks delimit the value
if level + dB_Correction < cutoff
    level = adjust_low_levels(level, cutoff, slope);
end
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

