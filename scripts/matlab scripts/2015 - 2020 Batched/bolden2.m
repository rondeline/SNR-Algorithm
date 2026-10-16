function bolden2(out_file, N, ranges)
% see
% https://www.mathworks.com/matlabcentral/answers/95627-how-do-i-set-the-letters-in-an-excel-sheet-cell-to-bold-through-actxserver-using-matlab-7-8-r2009
e = actxserver('Excel.Application');
e.Workbooks.Open(out_file);
sheet = e.ActiveWorkbook.Sheets.Item(N);
sheet.Activate
for k = 1:length(ranges)
    cells = e.ActiveSheet.Range(ranges{k});
    set(cells.Font, 'Bold', true)
end

wide_ranges = {'B1' 'C1' 'D1' 'E1' 'F1' 'G1' 'H1'};
widths = [28 12 15 20 20 20 20];
% also set column widths wider
for k = 1:length(wide_ranges)
    NewRange = sheet.Range(wide_ranges{k});
    NewRange.ColumnWidth = widths(k);
    % center text
    NewRange.EntireColumn.HorizontalAlignment = 3;
    % https://www.mathworks.com/matlabcentral/answers/216917-can-matlab-pre-format-individual-cells-when-writing-data-to-an-excel-spreadsheet
end

e.ActiveWorkbook.Save;
e.ActiveWorkbook.Close;
e.Quit
e.delete
