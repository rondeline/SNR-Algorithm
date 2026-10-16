function time_val = checkstring(time_str)
% function to check format of string time_str.
% If it's valid, return the double value
if ~strcmp(time_str(1:2), 'PT')
    disp(['PT not found at start of string (' time_str ')'])
    time_val = 0;
    return
end
if time_str(end) ~= 'S'
    disp(['S not found at end of string (' time_str ')'])
    return
end

time_val = str2double(time_str(3:end-1));

