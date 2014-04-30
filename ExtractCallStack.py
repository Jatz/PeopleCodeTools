import sublime, sublime_plugin, re
from .libs.regex import regex_extract
from .libs.regex import regex_findall
from .libs.regex import greedy_replace

class ExtractpccallstackCommand(sublime_plugin.TextCommand):
    
    def run(self, edit):
        self.edit = edit
        extractions = []      

        # First remove all lines that have a call method followed by a start-ext, since the start-ext is sufficient
        # For example: the following call method line will be ignored since there is a start-ext immediately after it:
        # PSAPPSRV.4556 (2426) 	 1-8760   14.05.07    0.000000       call method  SSF_CFS:SSF_CFQKey.SSFQKeyString #params=7
        # PSAPPSRV.4556 (2426) 	 1-8761   14.05.07    0.000000   >>> start-ext Nest=01 SSFQKeyString SSF_CFS.SSF_CFQKey.OnExecute
        regions = regex_findall(self, find='(.*call method.*\n)(?=.*start-ext)', flags=0, replace='', extractions=extractions)
        greedy_replace(self, extractions, regions)
        
        # Extract all lines containing start, end, Nest=, call int, call private, call method and End-Function        
        regex_extract(self, r'(((start|end).*Nest=.*)|(call (int|private|method).*)|End-Function.*)')
        
        view = self.view
        regions = view.sel()
        alltextreg = sublime.Region(0, view.size())
        allLines = ''
        lines = view.lines(alltextreg)
        y = 0
        lastCall = ''
        nestLevel = 0
        
        lastTabbedLineTabLength = 0
        
        for line in lines:
            y = y + 1
            lineContents = view.substr(line)
            # extract Nest value from lineContents
            match = re.search(r'(start|end).*Nest=(\d+)', lineContents)
            if match:                
                nestLevel = int(match.group(2))
                for x in range(0,nestLevel):
                    lineContents = '\t' + lineContents
                allLines = allLines + lineContents + '\n'
                    
                if match.group(1) == 'start':
                    lastCall = 'start'
                else:
                    if match.group(1) == 'end':
                        lastCall = 'end'
                                         
            else:
                match = re.search(r'(call int|End-Function)', lineContents)
                if match:
                    if match.group(1) == 'call int':
                        if lastCall == 'start':
                            nestLevel= nestLevel + 1
                        lastCall='callInt'    
                    else:                      
                        nestLevel = nestLevel - 1
                        lastCall='endFunction'
                
                for x in range(0,nestLevel):
                    lineContents = '\t' + lineContents

                if lastCall == 'start':
                    allLines = allLines + '\t' + lineContents + '\n'
                else:
                    allLines = allLines + lineContents + '\n'
                    
                if lastCall == 'callInt':
                    nestLevel = nestLevel + 1
            
        view.replace(edit, alltextreg, allLines)

        # Clean lines
        # Remove the end-ext, End-Function and end calls, since we no longer need them after formatting
        regex_extract(self, r'(.*(start).*Nest=.*)|.*(call (int|private|method).*)')

        # Remove unnecessary header junk (e.g. start, start-ext, Nest, etc.) 
        regions = regex_findall(self, find='((start.*Nest=\d\d)|(call (int|private|method)))[\s]*', flags=0, replace='', extractions=extractions)
        greedy_replace(self, extractions, regions)

        # Remove unnecessary trailer junk (e.g. params= or #params=)
        regions = regex_findall(self, find='[\s]#?params=\d+', flags=0, replace='', extractions=extractions)
        greedy_replace(self, extractions, regions) 
