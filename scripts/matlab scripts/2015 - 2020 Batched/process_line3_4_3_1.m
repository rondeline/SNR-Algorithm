function [start_time, end_time, level] = process_line3(text_line)
%PROCESS_LINE3  Read one <Segment .../> or <Pause .../> line from a LENA .its file
%   [T0 , T1 , LEVEL] = PROCESS_LINE3(TEXT_LINE)
%   * LEVEL returns NaN when the line has no "average_dB" attribute
%
%   Compatible with:
%     • ITS 4.6   – contains   average_dB=" … "
%     • ITS 4.3.x – loudness attributes absent
%
%   15-May-2025  JARVIS
% -------------------------------------------------------------------------

global dB_Correction                                      % (unchanged)

cutoff = 30;                                             % linear-correction parms
slope  = 0.4;

%% ---------- average_dB  (idk how we are gonna do this cause its kinda missing) -------------------------------

%default_dB = -60;
%level = default_dB;                                             % default for 4.3.x

level = NaN;
k = strfind(text_line,'average_dB="');                   % search once
if ~isempty(k)
    line1 = text_line(k(1)+length('average_dB="') : end);
    q     = find(line1=='"',1,'first')-1;                % up to next quote
    if ~isempty(q)
        level = str2double(line1(1:q));
        if (level + dB_Correction) < cutoff              % low-level adjust
            level = adjust_low_levels(level, cutoff, slope);
        end
    end
end

%% ---------- startTime ---------------------------------------------------
k = strfind(text_line,'startTime="');
if isempty(k)
    error('process_line3: startTime attribute not found');
end
line1 = text_line(k(1)+length('startTime="') : end);
q     = find(line1=='"',1,'first')-1;
start_time = checkstring(line1(1:q));

%% ---------- endTime -----------------------------------------------------
k = strfind(text_line,'endTime="');
if isempty(k)
    error('process_line3: endTime attribute not found');
end
line1 = text_line(k(1)+length('endTime="') : end);
q     = find(line1=='"',1,'first')-1;
end_time   = checkstring(line1(1:q));

end     % -------------------- END main function --------------------------


% ========================================================================
function time_val = checkstring(time_str)
% Return the numeric value inside a standard 'PTnnnS' time string
    if ~startsWith(time_str,'PT') || ~endsWith(time_str,'S')
        warning('process_line3: unexpected time string "%s"',time_str);
        time_val = NaN;
    else
        time_val = str2double(time_str(3:end-1));
    end
end
