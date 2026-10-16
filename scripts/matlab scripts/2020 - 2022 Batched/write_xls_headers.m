function out_file = write_xls_headers(filen, LENA_labels)
% function write_xls_headers(filen, LENA_labels)
% Open output file and write headers
% 5-Dec-2017

global xlsfileSTR

[pathn, fn] = fileparts(filen);
if isempty(pathn)
    pathn = pwd;
end

% output filename will be same as input, with '_stats' appended
out_file = [pathn filesep fn '_stats.xlsx'];

if exist(out_file)
    disp(['Output file ' out_file ' already exists.'])
    yn = input('Do you want to overwrite it? [y or n]: ', 's');
    if isempty(yn)  || upper(yn) ~= 'Y'
        out_file = [];
        disp('OK, exiting...')
        return
    end
    delete(out_file);
end

% write Sheet3 headers (summary stats)

Sheet3_name = xlsfileSTR.SheetNames{3};
start_row = xlsfileSTR.start_row3;


start_col = xlsfileSTR.start_col3;
end_col = start_col + length(LENA_labels) - 1;
rng_lab = [xlcolumnletter(start_col) int2str(start_row-1) ':' xlcolumnletter(end_col) int2str(start_row-1)];
xlswrite(out_file, LENA_labels, 'Sheet3', rng_lab);
rename_sheet(out_file, 3, Sheet3_name);    % rename the sheet

% write the other header info
H_Block = {'Segments Analyzed'; 'Segments Rejected'; 'Mean Duration (s)'; 'Mean Level (dB)'; 'Mean Level (Power)'; 'Median Level (dB)'; 'Median Level (Power)'};
xlsfileSTR.number_of_stats = length(H_Block);
rows_each_part = xlsfileSTR.number_of_stats + 2;
for k = 1:3
    switch k
        case 1
            BB = [{'Conversations'}; H_Block];
            rng{k} = ['A' int2str(start_row)];
        case 2
            BB = [{'Pauses'}; H_Block];
            rng{k} = ['A' int2str(start_row + rows_each_part)];
        case 3
            BB = [{'Total'}; H_Block];
            rng{k} = ['A' int2str(start_row + 2*rows_each_part)];
    end
    
    xlswrite(out_file, BB, Sheet3_name, rng{k})
end

xlswrite(out_file, {fn}, Sheet3_name, 'A1')  % file name
bolden(out_file, 3, [{'A1'} rng rng_lab])  % assume third sheet

% Now write Sheet1 headers (segment by segment listings)
write_sheet1_headers(out_file, LENA_labels, fn)
