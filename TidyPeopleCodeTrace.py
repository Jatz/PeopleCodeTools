import sublime, sublime_plugin, re
from .libs.regex import regex_extract
from .libs.regex import regex_findall
from .libs.regex import greedy_replace

SETTINGS_FILE = "PeopleCodeTools.sublime-settings"

class TidypctraceCommand(sublime_plugin.TextCommand):
    
    def run(self, edit):
        settings = sublime.load_settings(SETTINGS_FILE)
        self.edit = edit

        # Grab the current view contents and store it in a new file
        currentView = self.view;
        currentViewContent = currentView.substr(sublime.Region(0, currentView.size()))        
        newView = currentView.window().new_file()
        newViewAllTextRegion = sublime.Region(0, newView.size())
        newView.replace(edit, newViewAllTextRegion, currentViewContent)

        # Get location of syntax file
        currentSyntax = currentView.settings().get('syntax')

        ## Remove header junk
        if settings.get("tidy_remove_psappsrv_headers") == True:
            extractions = []
            regions = regex_findall(newView, find='(^PSAPPSRV.*?\d\.\d{6}\s)(.*)', flags=0, replace='\\2', extractions=extractions)
            greedy_replace(self, newView, extractions, regions)

            extractions = []
            regions = regex_findall(newView, find='(^PSAPPSRV.*@JavaClient.*IntegrationSvc\]\(\d\)\s{3})(.*)', flags=0, replace='\\2', extractions=extractions)
            greedy_replace(self, newView, extractions, regions)

        ## Fix up unmatched quotes
        if settings.get("tidy_add_unmatched_quotes") == True:
            extractions = []
            regions = regex_findall(newView, find='(.*"[^";\)\s>]+$)', flags=0, replace='\\1" - quote added by Tidy', extractions=extractions)
            greedy_replace(self, newView, extractions, regions)

            extractions = []
            regions = regex_findall(newView, find='(.*\("[^"]+$)', flags=0, replace='\\1" - quote added by Tidy', extractions=extractions)
            greedy_replace(self, newView, extractions, regions)

            extractions = []
            regions = regex_findall(newView, find='(.*="$)', flags=0, replace='\\1" - quote added by Tidy', extractions=extractions)
            greedy_replace(self, newView, extractions, regions)

            extractions = []
            regions = regex_findall(newView, find='(.*class="[^"\n]+$)', flags=0, replace='\\1" - quote added by Tidy', extractions=extractions)
            greedy_replace(self, newView, extractions, regions)
                
        
        ## Remove all blank spaces
        if settings.get("tidy_remove_blank_spaces") == True:
            extractions = []
            regions = regex_findall(newView, find='^\n', flags=0, replace='', extractions=extractions)
            greedy_replace(self, newView, extractions, regions)

        # Set syntax of new file and clear current selection
        newView.set_syntax_file(currentSyntax)
        newView.sel().clear()
