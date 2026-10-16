function write_block
% function write_block
% Function to write the block of data (generated
% with repeated calls to store_line) to excel file.

global xlsfileSTR
global grand_data_block
global grand_data_block2

rowx = xlsfileSTR.start_row1;
colx = xlsfileSTR.start_col1;
rng = [xlcolumnletter(colx) int2str(rowx)];

xlswrite(xlsfileSTR.out_file, grand_data_block, xlsfileSTR.SheetNames{1}, rng)
xlswrite(xlsfileSTR.out_file, grand_data_block2, xlsfileSTR.SheetNames{2}, rng)
