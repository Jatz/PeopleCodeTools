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


### Sublime Text Extract Call Stack tool

This tool will extract and format the call stack from a PeopleSoft trace file with a 4044 PeopleCode trace.

This tool ONLY applies to PeopleSoft Trace Files that have a PeopleCode trace value of 4044. Trace files that haven't been generated using the 4044 trace flags will not produce enough information for the tool to format the call stack. To use the tool, open a .tracesql file in Sublime Text and then run the "PeopleCode Tools: Extract PeopleCode Call Stack" command from the command palette.

### Sublime Text Tidy PeopleCode Trace tool

This tool will tidy up a trace file. At the moment all this tool does is add a matching quote to the end of certain lines that have an odd number of quotes. This tool ensures that the syntax highlighting of a PeopleCode trace file works correctly.
