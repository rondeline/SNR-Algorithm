function write_SNR_headings_2(filen, Wsheet)
% function write_SNR_headings_2(filen, Wsheet)
% Writes headers to designated file and worksheet
% 15-Sep-2019
% New version, to use pause following each conversation

global h1_row h2_row
global h2a_col h2b1_col h2b2_col
global h3_col h3_row
global LENA_labels
global headings2a

headings1 = {'Weighted Speech (dB)' 'SNR (dB)'};
headings2a = {'StartClock' 'EndClock' 'ElapsedTime' 'Conversation Number' 'Pause Number' 'Conv. Start' 'Conv. End' 'Conv. Dur (s)' 'Pause Start' 'Pause End' 'Pause Dur (s)'...
    'OLN(c)(dB)' 'OLF(c) (dB)' 'OLN(p) (dB)' 'OLF(p) (dB)' 'Weighted Noise (dB)'};


headings2b = {'Female' 'FAN' 'FAF' 'Male' 'MAN' 'MAF' 'Other Ch' 'CXN' 'CXF' 'Comb-All' 'Combined-N' 'Combined-F' 'NaN' 'CHN' 'CHF'};

h3_col = 2;
h3_row = 1;

h1_row = 2;     % starting row for upper headings
h2_row = h1_row + 1;  % starting row for next (main) headings
skip1 = 1;   % number of columns to skip between headings2a and headings2b;
skip2 = 2;   % number of columns to skip between the two instances of headings2b

h2a_col = h3_col + 7 + 2*skip2;   % starting column for primary headings
h2b1_col = h2a_col + length(headings2a) + skip1 + 2;    % column for 1st set of headings 2b - skip columns
h2b2_col = h2b1_col + length(headings2b) + skip2;   % column for 2nd set of headings 2b - skip columns

xlswrite(filen, headings1(1), Wsheet, [xlcolumnletter(h2b1_col) int2str(h1_row)])
xlswrite(filen, headings1(2), Wsheet, [xlcolumnletter(h2b2_col) int2str(h1_row)])

xlswrite(filen, headings2a, Wsheet, [xlcolumnletter(h2a_col) int2str(h2_row)])
xlswrite(filen, {'Weighted Mean'}, Wsheet, [xlcolumnletter(h2a_col) int2str(h2_row+1)]) % row heading for mean
xlswrite(filen, headings2b, Wsheet, [xlcolumnletter(h2b1_col) int2str(h2_row)])
xlswrite(filen, headings2b, Wsheet, [xlcolumnletter(h2b2_col) int2str(h2_row)]) 

%%%%
% Now for headings for 2nd portion of the file (leftmost part of
% spreadsheet)
headings3 = {'Conversations' NaN NaN NaN 'Pauses'};
headings4 = {'Number' 'Dur(s)' 'Prop. Dur.'};

label_names = [LENA_labels NaN {'Total'}]';   % make into a column, adding a line for "Total"
xlswrite(filen, label_names, Wsheet, [xlcolumnletter(h3_col) int2str(h3_row+3)])
xlswrite(filen, headings3, Wsheet, [xlcolumnletter(h3_col+1) int2str(h3_row)])
xlswrite(filen, headings4, Wsheet, [xlcolumnletter(h3_col+1) int2str(h3_row+2)])
xlswrite(filen, headings4, Wsheet, [xlcolumnletter(h3_col+5) int2str(h3_row+2)])


% need to bolden all headings, center in cells, and merge some cells
% function bolden2(out_file, N, ranges)

e = actxserver('Excel.Application');
e.Workbooks.Open(filen);

% first bolden
sheet = e.ActiveWorkbook.Sheets.Item(Wsheet);
col_first = h2a_col;
col_last = h2b2_col + length(headings2b) - 1;
row_first = h1_row;
row_last = h2_row+1;

range_all_headings = [xlcolumnletter(col_first) int2str(row_first) ':' xlcolumnletter(col_last) int2str(row_last)];
sheet.Activate
    cells = e.ActiveSheet.Range(range_all_headings);
    set(cells.Font, 'Bold', true)
    rang2 = [xlcolumnletter(h3_col) int2str(h3_row+3) ':' xlcolumnletter(h3_col) int2str(h3_row+3+length(label_names))];
    cells = e.ActiveSheet.Range(rang2);
    set(cells.Font, 'Bold', true)
    rang3 = [xlcolumnletter(h3_col+1) int2str(h3_row) ':' xlcolumnletter(h3_col+7) int2str(h3_row+2)];
    cells = e.ActiveSheet.Range(rang3);
    set(cells.Font, 'Bold', true)

% next widen columns. 1st column and "Weighted noise" column are wider, blank columns are narrower, all others to 12
% also, center data in cells
col_WN = col_first + length(headings2a) - 1;  % column for weighted noise
col_blank1 = h2b1_col + length(headings2b) - 3;  % empty columns
col_blank2 = h2b2_col + length(headings2b) - 3;
for kol = col_first:col_last
    switch kol
        case col_first
            width = 28;
        case col_WN
            width = 20;
        case {col_blank1 col_blank2}
            width = 8;
        otherwise
            width = 12;
    end
    range = [xlcolumnletter(kol) '1'];
    NewRange = sheet.Range(range);
    NewRange.ColumnWidth = width;
    NewRange.EntireColumn.HorizontalAlignment = 3;   % center text
end

% same thing for right-most table
% for kol = h3_col:h3_col+5
%     range = [xlcolumnletter(kol) '1'];
%     NewRange = sheet.Range(range);
%     NewRange.EntireColumn.HorizontalAlignment = 3;   % center text
% end


% For centering text:
%     
%     % https://www.mathworks.com/matlabcentral/answers/216917-can-matlab-pre-format-individual-cells-when-writing-data-to-an-excel-spreadsheet
% end

% now merge cells for the first level headings

col_stop1 = h2b1_col + length(headings2b) - 1;
col_stop2 = h2b2_col + length(headings2b) - 1;

rang1 = [xlcolumnletter(h2b1_col) int2str(h1_row) ':' xlcolumnletter(col_stop1) int2str(h1_row)];
rang2 = [xlcolumnletter(h2b2_col) int2str(h1_row) ':' xlcolumnletter(col_stop2) int2str(h1_row)];

x = sheet.get('Range', rang1);
x.MergeCells = 1;
y = sheet.get('Range', rang2);
y.MergeCells = 1;

% for table of durations

rang3 = [xlcolumnletter(h3_col+1) int2str(h3_row) ':' xlcolumnletter(h3_col+2) int2str(h3_row)];
rang4 = [xlcolumnletter(h3_col+4) int2str(h3_row) ':' xlcolumnletter(h3_col+5) int2str(h3_row)];

x = sheet.get('Range', rang3);
x.MergeCells = 1;
y = sheet.get('Range', rang4);
y.MergeCells = 1;

e.ActiveWorkbook.Save;
e.ActiveWorkbook.Close;
e.Quit
e.delete
