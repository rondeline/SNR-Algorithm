function Inclusion_Boundaries = get_inclusion_times(filen)
% function Inclusion_Boundaries = get_inclusion_times(filen)
% Function to read in inclusion times (in seconds)
% 9-Dec-2017

[pathn, fn] = fileparts(filen);

% Inclusion filename will be same as input, with '.xlsx extension
incl_file = [pathn filesep fn '.xlsx'];

if ~exist(incl_file)
    disp(['Could not find inclusion file ' incl_file '. Exiting...'])
    Inclusion_Boundaries = 0;
    return
else
    indx = 0;
    while 1
        indx = indx + 1;
        rng = ['B' int2str(indx+1) ':C' int2str(indx+1)];
        Limits = xlsread(incl_file, rng);
        if isempty(Limits)
            break
        else
            Inclusion_Boundaries(indx, 1:2) = Limits;
        end
    end
end
        
        
