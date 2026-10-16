function [pause_segment, pause_number] = get_following_pause(textstring)
% function [pause_segment, pause_number] = get_following_pause(textstring)
% function to get pause immediately following the conversation (which
% will be in the first part of string textstring)

x = findstr(textstring, 'Pause CHF');
if isempty(x)
    pause_number = 0;   % no pause found
    pause_segment = '';
    return
end

y = findstr(textstring, 'Pause>');
pause_segment = textstring(x(1):y(1));

% get pause number
x = findstr(pause_segment, 'num="');
Num_Start = x(1)+5;
x = findstr(pause_segment(Num_Start+1:end), '"');
Num_end = Num_Start-1+x(1);
val_s = pause_segment(Num_Start:Num_end);
pause_number = str2double(val_s);
