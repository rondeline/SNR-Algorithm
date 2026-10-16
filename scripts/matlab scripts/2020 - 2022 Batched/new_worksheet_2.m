function sheet_no = new_worksheet_2(SNR_output_file, sheetname)
% function sheet_no = new_worksheet_2(SNR_output_file, sheetname)
% 5 June 2018
% function to write the headers
% First see if this sheet already exists

[~, B] = xlsfinfo(SNR_output_file); % get sheet names

ix = find(strcmp(B, sheetname));
if isempty(ix)
    disp(['Creating new Worksheet: ' sheetname])
    e = actxserver('Excel.Application');
    ewb = e.Workbooks.Open(SNR_output_file);
    WS = ewb.Worksheets;
    WS.Add([], WS.Item(WS.Count));  % (see https://www.mathworks.com/matlabcentral/answers/2603-add-a-new-excel-sheet-from-matlab)
    WS.Item(WS.Count).Name = sheetname;
    sheet_no = WS.Count;
    ewb.Save
    ewb.Close(false)
    write_SNR_headings_2(SNR_output_file, sheet_no)
    xlswrite(SNR_output_file, {sheetname}, sheetname, 'A1')  % id at upper left
    bolden(SNR_output_file, sheet_no, {'A1'})   % bolden it
else
    disp(['Worksheet ' sheetname ' already exists.'])
%     yn = input('Do you want to write over this worksheet? ', 's');
yn = 'y';
    if isempty(yn) || upper(yn) ~= 'Y'
        disp('OK, exiting...')
        return
    else   % delete the contents of this page (see https://www.mathworks.com/matlabcentral/answers/642-how-do-i-clear-the-contents-of-excel-by-sheet)
        e = actxserver('Excel.Application');
        ewb = e.Workbooks.Open(SNR_output_file);
        cellfun(@(x) e.ActiveWorkBook.Sheets.Item(x).Cells.Clear, B(ix));
        ewb.Save
        ewb.Close(false)
        write_SNR_headings_2(SNR_output_file, ix)
        xlswrite(SNR_output_file, {sheetname}, sheetname, 'A1')  % id at upper left
        bolden(SNR_output_file, ix, {'A1'})   % bolden it
        sheet_no = ix;
    end
end


