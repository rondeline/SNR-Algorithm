function new_level = adjust_low_levels(level, cutoff, slope)
% function new_level = adjust_low_levels(level, cutoff, slope)
% applies linear correction to levels below the cutoff level,
% to adjust for the expansion produced by the LENA device.

global dB_Correction
lev = level + dB_Correction;
new_lev = lev*slope + cutoff;
new_level = new_lev - dB_Correction;  % convert back to "uncorrected" level

