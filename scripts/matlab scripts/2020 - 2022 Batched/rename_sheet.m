function rename_sheet(out_file, N, newname)
% rename the sheet in this file
% (see
% https://www.mathworks.com/matlabcentral/answers/215703-changing-the-name-of-the-sheet-in-excel)

% (for deleting sheets, see:
% https://www.mathworks.com/matlabcentral/answers/92449-how-can-i-delete-the-default-sheets-sheet1-sheet2-and-sheet3-in-excel-when-i-use-xlswrite
% )

e = actxserver('Excel.Application');
ewb = e.Workbooks.Open(out_file);
ewb.Worksheets.Item(N).Name = newname;
ewb.Save
ewb.Close(false)
e.Quit