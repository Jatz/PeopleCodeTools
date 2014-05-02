# PeopleCode Tools - Sublime Plugin

This repository contains the following:
- Sublime Text Syntax Highlighter for PeopleCode and PeopleSoft Trace files
- Sublime Text Extract Call Stack tool
- Sublime Text Tidy PeopleCode Trace tool

### Sublime Text Syntax Highlighter for PeopleCode and PeopleSoft Trace files

The syntax highlighter applies to files with the following extensions:
- ppl (PeopleCode)
- pcode (PeopleCode)
- tracesql (PeopleSoft Trace Files)
- trc (PeopleSoft COBOL Trace Files)

Note: This tool will not work so well on large files (i.e. files greater than 8 MB)

### Sublime Text Extract Call Stack tool

This tool will extract and format the call stack from a PeopleSoft trace file with a 4044 PeopleCode trace.

This tool ONLY applies to PeopleSoft Trace Files that have a PeopleCode trace value of 4044. Trace files that haven't been generated using the 4044 trace flags will not produce enough information for the tool to format the call stack. To use the tool, open a .tracesql file in Sublime Text and then run the "PeopleCode Tools: Extract PeopleCode Call Stack" command from the command palette.

### Sublime Text Tidy PeopleCode Trace tool

This tool will tidy up a tracesql file by performing the following operations:
- Adding a matching quote to the end of certain lines that have an odd number of quotes, ensuring that the syntax highlighting of the PeopleCode trace file works correctly (tidy_add_unmatched_quotes). 
- Removing blank spaces (tidy_remove_blank_spaces)
- Removing the PSAPPSRV header text to make the trace file easier to read (tidy_remove_psappsrv_headers). This option is disabled by default. Feel free to set this to true in the user settings for this plugin if you desire this functionality.

Note: This tool may take a while to run on large files (i.e. files greater than 8 MB).

### Demonstration
To see how this plugin can be used refer to the following:
- <a href="http://www.jaymathew.com/?p=588" target="_blank">Using Syntax highlighting and the Tidy PeopleCode Trace tool</a>
<br>
- <a href="http://www.jaymathew.com/?p=18140" target="_blank">Using the Extract PeopleCode Call Stack tool</a>

