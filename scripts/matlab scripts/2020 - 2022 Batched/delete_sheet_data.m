% https://www.mathworks.com/matlabcentral/answers/642-how-do-i-clear-the-contents-of-excel-by-sheet


[~, sheetNames] = xlsfinfo(filename);
% Open Excel as a COM Automation server
Excel = actxserver('Excel.Application');
% Open Excel workbook
Workbook = Excel.Workbooks.Open(filename);
% Clear the content of the sheets (from the second onwards)
cellfun(@(x) Excel.ActiveWorkBook.Sheets.Item(x).Cells.Clear, sheetNames(2:end));
% Now save/close/quit/delete
Workbook.Save;
Excel.Workbook.Close;
invoke(Excel, 'Quit');
delete(Excel)
