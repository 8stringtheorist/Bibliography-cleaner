@echo off
REM change 'python' to 'python3' or accordingly, depending on how python is called in your system's variables.
REM Change also "samble.bib" file to the name of the one that you want it to read.
REM The "sample_clean.bib" can be modified to generate an output file with a custom name as well. 
python bib_clean_and_map.py sample.bib sample_clean.bib
