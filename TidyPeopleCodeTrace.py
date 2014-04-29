import sublime, sublime_plugin, re
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

        ## Fix up unmatched quotes  
        extractions = []
        regions = regex_findall(self, find='(.*"[^";\)\s>]+$)', flags=0, replace='\\1"', extractions=extractions)
        greedy_replace(self, extractions, regions)

        extractions = []
        regions = regex_findall(self, find='(.*="$)', flags=0, replace='\\1"', extractions=extractions)
        greedy_replace(self, extractions, regions)

        ## Remove header junk
        extractions = []
        regions = regex_findall(self, find='(^PSAPPSRV.*?\d\.\d{6}\s)(.*)', flags=0, replace='\\2', extractions=extractions)
        greedy_replace(self, extractions, regions)        
        
        ## Remove all blank spaces
        extractions = []
        regions = regex_findall(self, find='^\n', flags=0, replace='', extractions=extractions)
        greedy_replace(self, extractions, regions)
