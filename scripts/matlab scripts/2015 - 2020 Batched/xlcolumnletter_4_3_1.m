function col = xlcolumnletter_4_3_1(n)
%XL COLUMNLETTER Convert 1-based column index to Excel column letters.
%   col = xlcolumnletter(1)   returns 'A'
%   col = xlcolumnletter(27)  returns 'AA'
%   Supports n = 1 ... 702 ('A' ... 'ZZ')

    if n < 1 || n > 702
        error('xlcolumnletter: n must be an integer between 1 and 702.');
    end

    col = '';
    while n > 0
        r   = mod(n-1, 26);          % remainder 0-25
        col = [char(65 + r) col];    % prepend letter
        n   = floor((n-1) / 26);     % next digit
    end
end
