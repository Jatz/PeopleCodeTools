import sublime, sublime_plugin
from PeopleCodeTools.regex import regex_extract
from PeopleCodeTools.regex import regex_findall
from PeopleCodeTools.regex import greedy_replace

class TidypctraceCommand(sublime_plugin.TextCommand):
    
    def run(self, edit):
        self.edit = edit
        view = self.view
        regions = view.sel()
        alltextreg = sublime.Region(0, view.size())
        lines = view.lines(alltextreg)
        allLines = ''
        
        for line in lines:
            lineContents = view.substr(line)
            quoteCount = 0
            for char in lineContents:
                if char == '"':
                    quoteCount = quoteCount + 1

            if (quoteCount % 2) != 0:
                lineContents = lineContents + '"'
                
            allLines = allLines + lineContents + '\n'                        
        
        view.replace(edit, alltextreg, allLines)

        extractions = []

        ## Remove all blank spaces
        regions = regex_findall(self, find='^\n', flags=0, replace='', extractions=extractions)
        greedy_replace(self, extractions, regions)
