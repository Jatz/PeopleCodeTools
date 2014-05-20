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
        # PSAPPSRV.4556 (2426)   1-8761   14.05.07    0.000000   >>> start-ext Nest=01 SSFQKeyString SSF_CFS.SSF_CFQKey.OnExecute getter
        newViewString = re.sub(r'(?m)(?:.*call\s+(getter|setter|method|constructor).*)\n(.*>>>\sstart-ext.*)', r'\2 \1', originalViewContent)

        # Add an end-get for relevant lines
        # I.e. Find all internal call getters and add end-gets. This is done by matching line number before the call getter and after the getter method has finished
        # Note: This is really ugly, but I couldn't find a better way to do this. Plus it's all 'easily' done in one line of code
        newViewString = re.sub(r'(\d+:.*)(\n.*call getter\s+(?:\w+:?)+\.\w+[\s\S]*?)(.*)(\1)', r'\1\2\3end-get;', newViewString)

        # First, remove all end-sets as they don't seem to always be there. Next, re-add an end-set for relevant lines
        # Note: Once again, this is really ugly, but I couldn't find a better way to do this. I wish the trace always showed end-set and end-get statements!!
        newViewString = re.sub(r'.*end-set;', '', newViewString)
        newViewString = re.sub(r'(.*call setter\s+(?:\w+:?)+\.(\w+).*)([\s\S]+?set\s\2[\s\S]+?[\s\S]+?)(Str\[\d+\]=\2)', r'\1\3end-set;', newViewString)

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

            # extContext will store a list of contexts to keep track of all the start and start-ext calls
            extContext = []

            # Perform initial formatting based on Nest value
            for lineContents in lines:
                # extract Nest value from lineContents
                match = re.search(r'(start-ext|start|end-ext|end|resume|reend)\s+Nest=(\d+)', lineContents)
                if match:
                    nestLevel = int(match.group(2)) - lowestNestValue

                    startIndex = 0

                    for x in range(startIndex,nestLevel):
                        lineContents = '\t' + lineContents
                    sessionSpecificString = sessionSpecificString + lineContents + '\n'

                    if match.group(1) == 'start':
                        lastCall = 'start'
                        # E.g. >>> start     Nest=12  DERIVED_ADDR.ADDRESSLONG.RowInit
                        matchExt = re.search(r'start\s+Nest=(?:\d+).*?((?:\w+\.?)+)', lineContents)
                        extContext.append(matchExt.group(1))
                    if match.group(1) == 'start-ext':
                        lastCall = 'start'
                        # keep track of start-ext location so that we can append the location to call private and call int lines
                        # E.g. >>> start-ext Nest=14 ActivePrograms_SCT SSR_STUDENT_RECORDS.SR_StudentData.StudentActivePrograms.OnExecute
                        matchExt = re.search(r'start-ext\s+Nest=(?:\d+)\s+\w+\s+((?:\w+\.?)+)', lineContents)
                        extContext.append(matchExt.group(1))
                    if  match.group(1) == 'resume':
                        lastCall = 'resume'
                    if match.group(1) == 'end-ext':
                        lastCall = 'end'
                        # remove the last element from extContext
                        extContext.pop()
                    if match.group(1) == 'end':
                        lastCall = 'end'
                        # remove the last element from extContext
                        extContext.pop()
                    if match.group(1) == 'reend':
                        lastCall = 'reend'

                else:
                    match = re.search(r'(call (int|setter|getter|private|method)|End-Function|end-get|end-set)', lineContents)
                    if match:
                        # if first 4 chars are 'call'
                        if match.group(1)[:4] == 'call':

                            if lastCall in ['start', 'resume'] or (lastCall[:4] == 'call'):
                                nestLevel += 1

                            if match.group(1) == 'call method':
                                lastCall = 'callMethod'
                                # Rearrange lines so that the method is at the start (like all other lines)
                                lineContents = re.sub(r'call method\s+((?:\w+:?)+)\.(\w+)', r'call \2 \1.OnExecute', lineContents)

                            if match.group(1) == 'call getter':
                                lastCall = 'callGetter'
                                # Rearrange the call getter so that it is in the same format as all the other calls
                                lineContents = re.sub(r'call getter\s+((?:\w+:?)+)\.(\w+)', r'call getter \2 \1.OnExecute', lineContents)

                            if match.group(1) == 'call setter':
                                lastCall = 'callSetter'
                                # Remove extra space after call setter and also rearrange setter so that it is at the start (like all other lines)
                                # E.g. call setter  EO:CA:Address.EditPageHeader
                                lineContents = re.sub(r'call setter\s+((?:\w+:?)+)\.(\w+)', r'call setter \2 \1.OnExecute', lineContents)

                            if match.group(1) == 'call private':
                                lastCall = 'callPrivate'
                                # Now we need to append the last value in extContext (i.e. extContext[-1])
                                lineContents = re.sub(r'call private\s+(\w+)', r'call \1 %s' % extContext[-1], lineContents)

                            if match.group(1) == 'call int':
                                lastCall = 'callInt'
                                # Now we need to append the last value in extContext (i.e. extContext[-1])
                                lineContents = re.sub(r'call int\s+(\w+)', r'call \1 %s' % extContext[-1], lineContents)


                        else:
                            if match.group(1)[:3].lower() == 'end':
                                if match.group(1) == 'End-Function':
                                    lastCall ='endFunction'
                                if match.group(1) == 'end-get':
                                    lastCall = 'endGet'
                                if match.group(1) == 'end-set':
                                    lastCall = 'endSet'
                                nestLevel -= 1

                    startIndex = 0

                    for x in range(startIndex,nestLevel):
                        lineContents = '\t' + lineContents

                    if lastCall == 'start':
                        sessionSpecificString = sessionSpecificString + '\t' + lineContents + '\n'
                    else:
                        sessionSpecificString = sessionSpecificString + lineContents + '\n'

                prevLineContents = lineContents

            # Remove Nest from each line since we no longer need it
            sessionSpecificString = re.sub(r'\s+Nest=\d+', '', sessionSpecificString)

            # Remove unnecessary trailer junk (e.g. params= or #params=)
            sessionSpecificString = re.sub(r'Dur=.*', '', sessionSpecificString)
            sessionSpecificString = re.sub(r'[\s]#?params=\d+', '', sessionSpecificString)

            # Are there any resume or reend statements?
            # If so, then reformat the session specific string based on the resume and reend statements
            found = re.search('(resume|reend)\s(.*)', sessionSpecificString)
            if found:
                # first remove any dots straight after the resume/reend (if there are any)
                sessionSpecificString = re.sub(r'(resume|reend)\s+\.\s+(.*)', r'\1 \2', sessionSpecificString)

                # Store remaining text line by line in a dict called results
                lines = sessionSpecificString.split('\n')
                results = {}
                lineNo = 1
                for lineContents in lines:
                    results[lineNo] = lineContents
                    lineNo = lineNo + 1

                resumeResults = {}
                reendResults = {}
                endResults = {}

                # Find resume and reend statements and store the line numbers in a dict along with the results
                for lineNo, line in results.items():
                    match = re.search(r'(resume|reend|end)\s.*?((?:\w+\.?)+((?:\s(?:\w+\.?)+)?))', line)
                    if match:
                        if match.group(1) == 'resume':
                            resumeResults[lineNo] = match.group(2)
                        if match.group(1) == 'reend':
                            reendResults[lineNo] = match.group(2)
                        if match.group(1) == 'end':
                            endResults[lineNo] = match.group(2)

                # Add a tab to each line before resume until you reach an end for that event
                for resumeResultLineNo, resumeResultLine in resumeResults.items():
                    # If there is actually an end within the same session, then format all lines after the end and before the resume
                    if resumeResultLine in endResults.values():
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
                        match = re.search(r'resume\s.*?%s' % reendResultLine, results[x])
                        if match:
                            break;
                        else:
                            if x != reendResultLineNo:
                                results[x] = '\t' + results[x]

                # store results in sessionSpecificString
                sessionSpecificString = ''
                for lineNo, line in results.items():
                    sessionSpecificString = sessionSpecificString + results[lineNo] + '\n'

            # Clean lines
            # Remove the end-ext, End-Function, end and reend calls, since we no longer need them
            str_list = re.findall(r'(?:.*(?:start|resume).*)|.*(?:call\s.*)', sessionSpecificString, re.MULTILINE)
            sessionSpecificString = '\n'.join(str_list)

            # Prefix all calls with suffix .OnExecute (apart from getter, setter and app engine steps) with call method
            sessionSpecificString = re.sub(r'(?m)call\s(?!(?:getter|setter))(.*\.OnExecute)$', r'call method \1', sessionSpecificString)

            # Prefix all remaining calls with call function
            sessionSpecificString = re.sub(r'(?m)call\s(?!(?:method|getter|setter))(.*(?!\.OnExecute))$', r'call function \1', sessionSpecificString)

            # Rename eligible call methods to call constructors
            sessionSpecificString = re.sub(r'(?m)(?m)call\smethod\s+(\w+)(\s.*\1.OnExecute)', r'call constructor \1\2', sessionSpecificString)

            # # Rename to call function those start-ext calls that do not have getters, setters or constructors appended
            sessionSpecificString = re.sub(r'(?m)start-ext\s(\w+)\s(\w+\.\w+\.\w+)$', r'call function \1 \2', sessionSpecificString)

            # # Replace any remaining start-ext with calls based on the last word in the line
            # # e.g. start-ext isSaveWarning PT_NAV2.NavOptions.OnExecute getter
            # # becomes call getter isSaveWarning PT_NAV2.NavOptions.OnExecute
            sessionSpecificString = re.sub('start-ext\s(\w+)\s(.*)\s(constructor|method|getter|setter)', r'call \3 \1 \2', sessionSpecificString)

            # Finally rename CI functions
            sessionSpecificString = re.sub(r'(?m)start-ext\s(\w+)\s(\w+\.\w+)$', r'call function (CI) \1 \2', sessionSpecificString)


            # # Replace any colons with dots
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

        # Set Syntax to PeopleCodeCallStack syntax
        newView.set_syntax_file('Packages/PeopleCodeTools/PeopleCodeCallStack.tmLanguage')
