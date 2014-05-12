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
        newView = originalView.window().new_file()

        # First remove all lines that have a call method, call getter, or call setter followed by a start-ext, since the start-ext is sufficient
        # For example: the following call method line will be ignored since there is a start-ext immediately after it:
        # PSAPPSRV.4556 (2426)   1-8760   14.05.07    0.000000       call method  SSF_CFS:SSF_CFQKey.SSFQKeyString #params=7
        # PSAPPSRV.4556 (2426)   1-8761   14.05.07    0.000000   >>> start-ext Nest=01 SSFQKeyString SSF_CFS.SSF_CFQKey.OnExecute
        newViewString = re.sub(r'(.*call (getter|setter|method).*\n)(?=.*>>>\sstart-ext)', '', originalViewContent)

        # Add an end-get for relevant lines
        # I.e. Find all internal call getters and add end-gets. This is done by matching line number before the call getter and after the getter method has finished
        # Note: This is really ugly, but I couldn't find a better way to do this. Plus it's all done in one line of code
        newViewString = re.sub(r'(\d+:.*)(\n.*call getter\s+(?:\w+:?)+\.\w+[\s\S]*?)(.*)(\1)', r'\1\2\3end-get;', newViewString)

        # Extract all lines containing start, end, Nest=, call int, call private, call method and End-Function
        # Note: we ignore call constructor and call setter
        str_list = re.findall(r'(?:(?:.*(?:start|end|resume|reend).*Nest=.*)|(?:.*call (?:int|private|method|getter|setter).*)|.*End-Function.*|.*end-get.*|.*end-set.*)', newViewString, re.MULTILINE)
        newViewString = '\n'.join(str_list)

        # Get the unique session numbers and store them in a list
        sessionNos = re.findall(r'PSAPPSRV.\d+\s+\((\d+)\)', newViewString, re.MULTILINE)
        sessionNos = sorted(set(sessionNos))

        sessionCount = 1

        for sessionNo in sessionNos:

            # Extract only those lines relating to the sessionNo
            str_list = re.findall(r'PSAPPSRV\.\d+\s+\(%s\).*' % sessionNo, newViewString, re.MULTILINE)
            sessionSpecificString = '\n'.join(str_list)

            # Remove header junk for each of the lines
            str_list = re.findall(r'(?:(?:(?:start|end|resume|reend).*Nest=.*)|(?:call (?:int|private|method|getter|setter).*)|End-Function.*|end-get.*|end-set.*)', sessionSpecificString, re.MULTILINE)
            sessionSpecificString = '\n'.join(str_list)

            # Get all the Nest values and store them in a list and store the lowest Nest value
            nestNos = re.findall(r'Nest=(\d+)', newViewString, re.MULTILINE)
            nestNos = sorted(set(nestNos))
            lowestNestValue = int(min(nestNos))

            # store lines in a list so that we can iterate through each line
            lines = sessionSpecificString.split('\n')

            sessionSpecificString = ''
            lastCall = ''
            nestLevel = 0

            # extContext will store a list of contexts to keep track of all the start-ext calls
            extContext = []

            # Perform initial formatting based on Nest value
            for lineContents in lines:
                # extract Nest value from lineContents
                match = re.search(r'(start-ext|start|end-ext|end|resume|reend).*Nest=(\d+)', lineContents)
                if match:
                    nestLevel = int(match.group(2)) - lowestNestValue

                    startIndex = 0

                    for x in range(startIndex,nestLevel):
                        lineContents = '\t' + lineContents
                    sessionSpecificString = sessionSpecificString + lineContents + '\n'

                    if match.group(1) == 'start':
                        lastCall = 'start'
                        # E.g. >>> start     Nest=12  DERIVED_ADDR.ADDRESSLONG.RowInit
                        matchExt = re.search(r'start.*Nest=(?:\d+).*?((?:\w+\.?)+)', lineContents)
                        extContext.append(matchExt.group(1))
                    if match.group(1) == 'start-ext':
                        lastCall = 'start'
                        # keep track of start-ext location so that we can append the location to call private and call int lines
                        # E.g. >>> start-ext Nest=14 ActivePrograms_SCT SSR_STUDENT_RECORDS.SR_StudentData.StudentActivePrograms.OnExecute
                        matchExt = re.search(r'start-ext.*Nest=(?:\d+).*\w+\s(.*)', lineContents)
                        extContext.append(matchExt.group(1))
                    if  match.group(1) == 'resume':
                        lastCall = 'resume'
                    if match.group(1) == 'end-ext':
                        lastCall = 'end'
                        # remove the last element from extContext
                        extContext.pop()
                    if match.group(1) == 'end':
                        lastCall = 'end'
                    if match.group(1) == 'reend':
                        lastCall = 'reend'

                else:
                    match = re.search(r'(call (int|setter|getter|private)|End-Function|end-get|end-set)', lineContents)
                    if match:
                        # if first 4 chars are 'call'
                        if match.group(1)[:4] == 'call':

                            if lastCall in ['start', 'resume'] or (lastCall[:4] == 'call'):
                                nestLevel = nestLevel + 1

                            if match.group(1) == 'call getter':
                                lastCall = 'callGetter'

                            if match.group(1) == 'call setter':
                                lastCall = 'callSetter'
                                # Remove extra space after call setter and also rearrange setter so that it is at the start (like all other lines)
                                # E.g. call setter  EO:CA:Address.EditPageHeader #params=3
                                lineContents = re.sub(r'call setter\s+((?:\w+:?)+)\.(\w+)', r'call setter \2 \1.OnExecute', lineContents)
                            if match.group(1) == 'call private':
                                lastCall = 'callPrivate'
                                # Now we need to append the last value in extContext (i.e. extContext[-1])
                                lineContents = re.sub(r'call private\s+(\w+)', r'call private \1 %s' % extContext[-1], lineContents)
                            if match.group(1) == 'call int':
                                lastCall = 'callInt'
                                # Now we need to append the last value in extContext (i.e. extContext[-1])
                                lineContents = re.sub(r'call int\s+(\w+)', r'call int \1 %s' % extContext[-1], lineContents)
                            else:
                                lastCall='call'
                        else:
                            if match.group(1) == 'End-Function':
                                lastCall ='endFunction'
                            if match.group(1) == 'end-get':
                                # End-Get reached
                                lastCall = 'endGet'
                            if match.group(1) == 'end-set':
                                # End-Get reached
                                lastCall = 'endSet'

                    startIndex = 0

                    for x in range(startIndex,nestLevel):
                        lineContents = '\t' + lineContents

                    if lastCall == 'start':
                        sessionSpecificString = sessionSpecificString + '\t' + lineContents + '\n'
                    else:
                        sessionSpecificString = sessionSpecificString + lineContents + '\n'

                    # if any of the last calls start with 'call'
                    if lastCall[:4] == 'call':
                        nestLevel = nestLevel + 1

                    if lastCall in ['endFunction', 'endGet', 'endSet']:
                        nestLevel = nestLevel - 1

            # Remove Nest from each line since we no longer need it
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
            str_list = re.findall(r'(?:.*(?:start).*)|.*(?:call (?:int|private|method|getter|setter).*)', sessionSpecificString, re.MULTILINE)
            sessionSpecificString = '\n'.join(str_list)

            # Rearrange the call getter so that it is in the same format as all the other calls
            sessionSpecificString = re.sub(r'call getter\s+((?:\w+(?::?))+)\.(\w+)', r'call getter \2 \1.OnExecute', sessionSpecificString)

            # Remove the start and call int/private/method strings from all lines as these strings are no longer required
            #sessionSpecificString = re.sub(r'(start|call (int|private|method|getter|setter)|start-ext)\s+', '', sessionSpecificString)

            # Remove unnecessary trailer junk (e.g. params= or #params=)
            sessionSpecificString = re.sub(r'Dur=.*', '', sessionSpecificString)
            sessionSpecificString = re.sub(r'[\s]#?params=\d+', '', sessionSpecificString)

            # Replace any colons with dots
            sessionSpecificString = re.sub(':', r'.', sessionSpecificString)

            # We now have the complete callstack for the session
            # Insert the call stack in the new view
            newViewAllTextRegion = sublime.Region(0, newView.size())
            if sessionCount == 1:
                newView.insert(edit, newViewAllTextRegion.end(), 'Session %s:\n' % sessionNo + sessionSpecificString)
            else:
                newView.insert(edit, newViewAllTextRegion.end(), '\n\nSession %s:\n' % sessionNo + sessionSpecificString)
            newView.sel().clear()

            # Increment session count, go to next sessionNo if available
            sessionCount += 1
