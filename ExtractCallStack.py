import sublime, sublime_plugin, re

class ExtractpccallstackCommand(sublime_plugin.TextCommand):

    # This method is only used for debugging
    def replaceViewContent(self, viewToReplace, replaceString):
        viewToReplaceAllTextRegion = sublime.Region(0, viewToReplace.size())
        viewToReplace.replace(self.edit, viewToReplaceAllTextRegion, replaceString)
        viewToReplace.sel().clear()
        
    def run(self, edit):
        self.edit = edit

        # Grab the current view contents and store it in a new file
        originalView = self.view;

        originalViewContent = originalView.substr(sublime.Region(0, originalView.size()))
        workingView = originalView.window().new_file()             
    
        # First remove all lines that have a call method followed by a start-ext, since the start-ext is sufficient
        # For example: the following call method line will be ignored since there is a start-ext immediately after it:
        # PSAPPSRV.4556 (2426)   1-8760   14.05.07    0.000000       call method  SSF_CFS:SSF_CFQKey.SSFQKeyString #params=7
        # PSAPPSRV.4556 (2426)   1-8761   14.05.07    0.000000   >>> start-ext Nest=01 SSFQKeyString SSF_CFS.SSF_CFQKey.OnExecute
        workingViewString = re.sub(r'(.*call method.*\n)(?=.*start-ext)', '', originalViewContent)
        
        # Extract all lines containing start, end, Nest=, call int, call private, call method and End-Function        
        str_list = re.findall(r'(?:(?:.*(?:start|end|resume|reend).*Nest=.*)|(?:.*call (?:int|private|method).*)|.*End-Function.*)', workingViewString, re.MULTILINE)
        workingViewString = '\n'.join(str_list)
        
        # Get the unique session numbers and store them in a list
        sessionNos = re.findall(r'PSAPPSRV.\d+\s+\((\d+)\)', workingViewString, re.MULTILINE)
        sessionNos = sorted(set(sessionNos))

        sessionCount = 1

        for sessionNo in sessionNos:

            # Extract only those lines relating to the sessionNo
            str_list = re.findall(r'PSAPPSRV\.\d+\s+\(%s\).*' % sessionNo, workingViewString, re.MULTILINE)
            sessionSpecificString = '\n'.join(str_list)

            # Remove header junk for each of the lines
            str_list = re.findall(r'(?:(?:(?:start|end|resume|reend).*Nest=.*)|(?:call (?:int|private|method).*)|End-Function.*)', sessionSpecificString, re.MULTILINE)
            sessionSpecificString = '\n'.join(str_list)

            # Get all the Nest values and store them in a list and store the lowest Nest value
            nestNos = re.findall(r'Nest=(\d+)', workingViewString, re.MULTILINE)
            nestNos = sorted(set(nestNos))
            lowestNestValue = int(min(nestNos))
                        
            # store lines in a list so that we can iterate through each line
            lines = sessionSpecificString.split('\n')
            
            sessionSpecificString = ''                    
            lastCall = ''
            nestLevel = 0
        
            # Perform initial formatting based on Nest value
            for lineContents in lines:
                # extract Nest value from lineContents
                match = re.search(r'(start|end|resume|reend).*Nest=(\d+)', lineContents)
                if match:                                       
                    nestLevel = int(match.group(2)) - lowestNestValue
                                        
                    startIndex = 0                               
                    
                    for x in range(startIndex,nestLevel):
                        lineContents = '\t' + lineContents
                    sessionSpecificString = sessionSpecificString + lineContents + '\n'                    

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
                        sessionSpecificString = sessionSpecificString + '\t' + lineContents + '\n'
                    else:
                        sessionSpecificString = sessionSpecificString + lineContents + '\n'
                        
                    if lastCall == 'callInt':
                        nestLevel = nestLevel + 1

            # Remove nest from the header
            sessionSpecificString = re.sub(r'\s+Nest=\d+', '', sessionSpecificString)

            # Are there any resume or reend statements?
            # If so, then reformat the session specific string based on the resume and reend statements
            found = re.search('(resume|reend)\s(.*)', sessionSpecificString)
            if found:
                # Store remaining text line by line in a dict called results
                lines = sessionSpecificString.split('\n')
                results = {}
                lineNo = 1
                for lineContents in lines:
                    results[lineNo] = lineContents
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

                sessionSpecificString = ''
                for lineNo, line in results.items():
                    sessionSpecificString = sessionSpecificString + results[lineNo] + '\n'
                                    

            # Clean lines
            # Remove the end-ext, End-Function, resume, end and reend calls, since we no longer need them
            str_list = re.findall(r'(?:.*(?:start).*)|.*(?:call (?:int|private|method).*)', sessionSpecificString, re.MULTILINE)
            sessionSpecificString = '\n'.join(str_list)           

            # Remove the start and call int/private/method strings from all lines as these strings are no longer required
            sessionSpecificString = re.sub(r'(start|call (int|private|method)|start-ext)\s+', '', sessionSpecificString)
            
            # Remove unnecessary trailer junk (e.g. params= or #params=)
            sessionSpecificString = re.sub(r'Dur=.*', '', sessionSpecificString)
            sessionSpecificString = re.sub(r'[\s]#?params=\d+', '', sessionSpecificString)

            # We now have the complete callstack for the session
            # Insert the call stack in the new view
            workingViewAllTextRegion = sublime.Region(0, workingView.size())
            if sessionCount == 1:
                workingView.insert(edit, workingViewAllTextRegion.end(), 'Session %s:\n' % sessionNo + sessionSpecificString)
            else:
                workingView.insert(edit, workingViewAllTextRegion.end(), '\nSession %s:\n' % sessionNo + sessionSpecificString)
            workingView.sel().clear()

            # Increment session count, go to next sessionNo if available
            sessionCount += 1
