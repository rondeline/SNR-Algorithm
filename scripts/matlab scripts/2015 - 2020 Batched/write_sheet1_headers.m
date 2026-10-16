function write_sheet1_headers(out_file, LENA_labels, fn)
% function write_sheet1_headers(LENA_labels)
% Writes headers to Sheet (detailed segment listings)
% (updated - now  writes to sheet2 as well as sheet1 - same headers to
% both)

global xlsfileSTR

Sheet1_name = xlsfileSTR.SheetNames{1};
Sheet2_name = xlsfileSTR.SheetNames{2};
sub_labels = xlsfileSTR.sub_labels;
columns_per_label = length(sub_labels) + 1;  % number of colums to allocate to each label
number_of_labels = length(LENA_labels);

row_labels = xlsfileSTR.start_row1 - 2;  % labels two rows above start of data
row_sublabels = row_labels + 1;
start_col = xlsfileSTR.start_col1;

% build the cell row of labels (with blanks interspersed between labels)
blanx = NaN * ones(columns_per_label-1, number_of_labels);
LENA2 = [LENA_labels; num2cell(blanx)];
LENA2 = LENA2(:)';   % make into one long row
% write it
xlswrite(out_file, LENA2, 'Sheet1', [xlcolumnletter(start_col) int2str(row_labels)])
xlswrite(out_file, LENA2, 'Sheet2', [xlcolumnletter(start_col) int2str(row_labels)])
rename_sheet(out_file, 1, Sheet1_name);    % rename the sheets
rename_sheet(out_file, 2, Sheet2_name);

% write the subheadings

for k = 1:number_of_labels
    colm = (k-1) * columns_per_label + start_col;
    rng = [xlcolumnletter(colm) int2str(row_sublabels)];  % found this function on web
    xlswrite(out_file, sub_labels, Sheet1_name, rng)
    xlswrite(out_file, sub_labels, Sheet2_name, rng)
end
    
xlswrite(out_file, {fn}, Sheet1_name, 'A1')  % file name at upper left
xlswrite(out_file, {fn}, Sheet2_name, 'A1')

% figure out cell ranges to bolden
% what column is last sub-label in (can use this for both labels and
% sub-labels
colm_last = colm + length(sub_labels) - 1;
colm_last_s = xlcolumnletter(colm_last);

all_ranges = {'A1' [xlcolumnletter(start_col) int2str(row_labels) ':' colm_last_s int2str(row_labels)] [xlcolumnletter(start_col) int2str(row_sublabels) ':' colm_last_s int2str(row_sublabels)]};
bolden(out_file, 1, all_ranges)
bolden(out_file, 2, all_ranges)
