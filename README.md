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

__Note:__ The syntax highlighting plugin slows the opening time for very large files (i.e. 50 MB or greater) due to the fact that the plugin uses regular expressions to create scopes. If you are using the BracketHighlighter plugin on large PeopleCode files, you’ll need to disable it by running ‘BracketHighlighter: Toggle Global Enable’ from the command line. If not, Sublime will behave very sluggishly for these files. Also, it is recommended that the ‘Highlight matches’ option be disabled when searching large files. If ‘Highlight matches’ is not disabled, the search will try to instantly match every single character you type.

### Sublime Text Extract Call Stack tool

This tool will extract and format the call stack from a PeopleSoft trace file.

This tool ONLY applies to PeopleSoft Trace Files that have a PeopleCode trace value between 2496 and 4044. Trace files that have not been generated using these trace flags will not produce enough information for the tool to format the call stack. To use the tool, open a .tracesql file in Sublime Text and then run the "PeopleCode Tools: Extract PeopleCode Call Stack" command from the command palette.

### Sublime Text Tidy PeopleCode Trace tool

This tool will tidy up a tracesql file by performing the following operations:
- Adding a matching quote to the end of certain lines that have an odd number of quotes, ensuring that the syntax highlighting of the PeopleCode trace file works correctly (tidy_add_unmatched_quotes). 
- Removing blank spaces (tidy_remove_blank_spaces)
- Removing the PSAPPSRV header text to make the trace file easier to read (tidy_remove_psappsrv_headers). This option is disabled by default. Feel free to set this to true in the user settings for this plugin if you desire this functionality.

__Note:__ This tool may take a while to run on large files (i.e. files greater than 8 MB).

### Demonstration
To see how this plugin can be used refer to the following:
- <a href="http://www.jaymathew.com/?p=588" target="_blank">Using Syntax highlighting and the Tidy PeopleCode Trace tool</a>
- <a href="http://www.jaymathew.com/?p=18140" target="_blank">Using the Extract PeopleCode Call Stack tool</a>
