function includ = check_inclusion(start_time, stop_time)
% function includ = check_inclusion(start_time, stop_time)
% function to return true or false, depending on whether any of the
% segment delimited by start_time and stop_time are within the
% boundaries specified in any of the rows of Inclusion_Boundaries

global Inclusion_Boundaries

nrows = size(Inclusion_Boundaries,1);

% check for each row. Can exit
includ = false;     % assume not included at first

for irow = 1:nrows
    t1 = Inclusion_Boundaries(irow,1);
    t2 = Inclusion_Boundaries(irow,2);
    if start_time >= t1 && start_time <= t2
        includ = true;   % start time is in range
        break;
    end
    if  stop_time >= t1 && stop_time <= t2
        includ = true;  % stop time is in range
        break;
    end
end
        
