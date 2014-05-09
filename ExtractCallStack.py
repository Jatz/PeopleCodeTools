import sublime, sublime_plugin, re
from .libs.regex import regex_extract
from .libs.regex import regex_findall
from .libs.regex import greedy_replace

class ExtractpccallstackCommand(sublime_plugin.TextCommand):

    def replaceCurrentViewContent(self, currentView, replaceString):
        currentViewAllTextRegion = sublime.Region(0, currentView.size())
        currentView.replace(self.edit, currentViewAllTextRegion, replaceString)
        currentView.sel().clear()
        
    def run(self, edit):
        self.edit = edit

        # Grab the current view contents and store it in a new file
        currentView = self.view;

        # Take a copy of the current view contents
        # Unfortunately if I copy the contents immediately to a new window and then perform the regex operations on it
        # the greedy_replace function will crash Sublime - not sure whether this is a bug with Sublime.
        currentViewContent = currentView.substr(sublime.Region(0, currentView.size()))
        newView = currentView.window().new_file()
        
        extractions = []

        # First remove all lines that have a call method followed by a start-ext, since the start-ext is sufficient
        # For example: the following call method line will be ignored since there is a start-ext immediately after it:
        # PSAPPSRV.4556 (2426) 	 1-8760   14.05.07    0.000000       call method  SSF_CFS:SSF_CFQKey.SSFQKeyString #params=7
        # PSAPPSRV.4556 (2426) 	 1-8761   14.05.07    0.000000   >>> start-ext Nest=01 SSFQKeyString SSF_CFS.SSF_CFQKey.OnExecute       
        regions = regex_findall(currentView, find='(.*call method.*\n)(?=.*start-ext)', flags=0, replace='', extractions=extractions)
        greedy_replace(self, currentView, extractions, regions) 
       
        # Extract all lines containing start, end, Nest=, call int, call private, call method and End-Function        
        regex_extract(self, currentView, r'((.*(start|end|resume|reend).*Nest=.*)|(.*call (int|private|method).*)|.*End-Function.*)')

        # Get the unique session numbers            
        sessionNos = []
        regions = regex_findall(currentView, find='PSAPPSRV.\d+\s+\((\d+)\).*', flags=0, replace='\\1', extractions=sessionNos)
        sessionNos = sorted(set(sessionNos))

        extractBackup = currentView.substr(sublime.Region(0, currentView.size()))

        sessionCount = 1
        for sessionNo in sessionNos:
            self.replaceCurrentViewContent(currentView, extractBackup)            
            regex_extract(self, currentView, r'PSAPPSRV.\d+\s+\((%s)\).*' % sessionNo)
            regex_extract(self, currentView, r'(((start|end|resume|reend).*Nest=.*)|(call (int|private|method).*)|End-Function.*)')
       
            alltextreg = sublime.Region(0, currentView.size())            
            allLines = ''
            lines = currentView.lines(alltextreg)            
            lastCall = ''
            nestLevel = 0
        
        
            for line in lines:
                lineContents = currentView.substr(line)
                # extract Nest value from lineContents
                match = re.search(r'(start|end|resume|reend).*Nest=(\d+)', lineContents)
                if match:                                       
                    nestLevel = int(match.group(2))
                                        
                    startIndex = 0                               
                    
                    for x in range(startIndex,nestLevel):
                        lineContents = '\t' + lineContents
                    allLines = allLines + lineContents + '\n'                    

                    if match.group(1) == 'start':
                        lastCall = 'start'
                    if  match.group(1) == 'resume':
                        lastCall = 'resume'
                    if match.group(1) == 'end':
                        lastCall = 'end'
                    if match.group(1) == 'reend':
                        lastCall = 'reend'
                                             
                else:
                    match = re.search(r'(call int|End-Function)', lineContents)
                    if match:
                        if match.group(1) == 'call int':
                            if (lastCall == 'start') | (lastCall == 'resume'):
                                nestLevel= nestLevel + 1
                            lastCall='callInt'    
                        else:                      
                            nestLevel = nestLevel - 1
                            lastCall='endFunction'

                    startIndex = 0
                    
                    for x in range(startIndex,nestLevel):
                        lineContents = '\t' + lineContents

                    if lastCall == 'start':
                        allLines = allLines + '\t' + lineContents + '\n'
                    else:
                        allLines = allLines + lineContents + '\n'
                        
                    if lastCall == 'callInt':
                        nestLevel = nestLevel + 1
                
            currentView.replace(edit, alltextreg, allLines)

            # Remove unnecessary header junk (e.g. start, start-ext, Nest, etc.)
            extractions = []
            regions = regex_findall(currentView, find='(?<=(start)).*Nest=\d\d', flags=0, replace='', extractions=extractions)
            greedy_replace(self, currentView, extractions, regions)

            extractions = []
            regions = regex_findall(currentView, find='(?<=(reend)).*Nest=\d\d\s\.', flags=0, replace='', extractions=extractions)
            greedy_replace(self, currentView, extractions, regions)    

            extractions = []
            regions = regex_findall(currentView, find='(?<=(end)).*Nest=\d\d', flags=0, replace='', extractions=extractions)
            greedy_replace(self, currentView, extractions, regions)

            extractions = []
            regions = regex_findall(currentView, find='(?<=(resume)).*Nest=\d\d\s\.', flags=0, replace='', extractions=extractions)
            greedy_replace(self, currentView, extractions, regions)   



            # Are there any resume or reend statements?
            extractions = []
            regions = regex_findall(currentView, find='^(resume|reend)\s(.*)', flags=0, replace='', extractions=extractions)
            if regions:
                # Store remaining text line by line in a dict called results
                alltextreg = sublime.Region(0, currentView.size())
                lines = currentView.lines(alltextreg)
                results = {}
                lineNo = 1
                for line in lines:
                    results[lineNo] = currentView.substr(line)
                    lineNo = lineNo + 1

                resumeResults = {}
                reendResults = {}
                # Find resume and reend statements and store the line numbers in a dict along with the results
                for lineNo, line in results.items():
                    match = re.search(r'^(resume|reend)\s(.*)', line)
                    if match:
                        if match.group(1) == 'resume':
                            resumeResults[lineNo] = match.group(2)
                        else:
                            reendResults[lineNo] = match.group(2)

                # Add a tab to each line before resume until you reach an end for that event
                for resumeResultLineNo, resumeResultLine in resumeResults.items():
                    for x in range(resumeResultLineNo,0, -1):
                        match = re.search(r'end\s+%s' % resumeResultLine, results[x])
                        if match:
                            break;
                        else:
                            if x != resumeResultLineNo:
                                results[x] = '\t' + results[x]

                # Add a tab to each line before reend until you reach a resume for that event
                for reendResultLineNo, reendResultLine in reendResults.items():
                    for x in range(reendResultLineNo,0, -1):
                        match = re.search(r'resume\s+%s' % reendResultLine, results[x])
                        if match:
                            break;
                        else:
                            if x != reendResultLineNo:
                                results[x] = '\t' + results[x]                        

                allLines = ''
                for lineNo, line in results.items():
                    allLines = allLines + results[lineNo] + '\n'
                    
                currentView.replace(edit, alltextreg, allLines)

            # Clean lines
            # Remove the end-ext, End-Function, resume, end and reend calls, since we no longer need them
            regex_extract(self, currentView, r'(.*(start).*)|.*(call (int|private|method).*)')

            # Remove start word from all lines as it is now superfluous
            extractions = []
            regions = regex_findall(currentView, find='(start|call (int|private|method))\s+', flags=0, replace='', extractions=extractions)
            greedy_replace(self, currentView, extractions, regions)

            # Remove unnecessary trailer junk (e.g. params= or #params=)
            extractions = []
            regions = regex_findall(currentView, find='Dur=.*', flags=0, replace='', extractions=extractions)
            greedy_replace(self, currentView, extractions, regions)

            extractions = []
            regions = regex_findall(currentView, find='[\s]#?params=\d+', flags=0, replace='', extractions=extractions)
            greedy_replace(self, currentView, extractions, regions)       

            # We now have the complete callstack for the session so store it in a string
            callStack = currentView.substr(sublime.Region(0, currentView.size()))

            # Insert the call stack in the new view
            newViewAllTextRegion = sublime.Region(0, newView.size())
            if sessionCount == 1:
                newView.insert(edit, newViewAllTextRegion.end(), 'Session %s:\n' % sessionNo + callStack)
            else:
                newView.insert(edit, newViewAllTextRegion.end(), '\nSession %s:\n' % sessionNo + callStack)
            newView.sel().clear()

            sessionCount += 1

        # Restore the current view to its original contents
        currentViewAllTextRegion = sublime.Region(0, currentView.size())
        currentView.replace(edit, currentViewAllTextRegion, currentViewContent)
        currentView.sel().clear()
