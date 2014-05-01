import sublime, sublime_plugin, re
from .libs.regex import regex_extract
from .libs.regex import regex_findall
from .libs.regex import greedy_replace

SETTINGS_FILE = "PeopleCodeTools.sublime-settings"

class TidypctraceCommand(sublime_plugin.TextCommand):
    
    def run(self, edit):
        settings = sublime.load_settings(SETTINGS_FILE)
        self.edit = edit
        view = self.view
        regions = view.sel()
        alltextreg = sublime.Region(0, view.size())
        lines = view.lines(alltextreg)
        allLines = ''

        ## Remove header junk
        if settings.get("tidy_remove_psappsrv_headers") == True:
            extractions = []
            regions = regex_findall(self, find='(^PSAPPSRV.*?\d\.\d{6}\s)(.*)', flags=0, replace='\\2', extractions=extractions)
            greedy_replace(self, extractions, regions)

            extractions = []
            regions = regex_findall(self, find='(^PSAPPSRV.*@JavaClient.*IntegrationSvc\]\(\d\)\s{3})(.*)', flags=0, replace='\\2', extractions=extractions)
            greedy_replace(self, extractions, regions)

        ## Fix up unmatched quotes
        if settings.get("tidy_add_unmatched_quotes") == True:
            extractions = []
            regions = regex_findall(self, find='(.*"[^";\)\s>]+$)', flags=0, replace='\\1" - quote added by Tidy', extractions=extractions)
            greedy_replace(self, extractions, regions)

            extractions = []
            regions = regex_findall(self, find='(.*\("[^"]+$)', flags=0, replace='\\1" - quote added by Tidy', extractions=extractions)
            greedy_replace(self, extractions, regions)

            extractions = []
            regions = regex_findall(self, find='(.*="$)', flags=0, replace='\\1" - quote added by Tidy', extractions=extractions)
            greedy_replace(self, extractions, regions)    
        
        ## Remove all blank spaces
        if settings.get("tidy_remove_blank_spaces") == True:
            extractions = []
            regions = regex_findall(self, find='^\n', flags=0, replace='', extractions=extractions)
            greedy_replace(self, extractions, regions)
