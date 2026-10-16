function bolden(out_file, N, ranges)
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

% also set first column width wider
NewRange = sheet.Range('A1');
NewRange.ColumnWidth = 25;
e.ActiveWorkbook.Save;
e.ActiveWorkbook.Close;
e.Quit
e.delete
