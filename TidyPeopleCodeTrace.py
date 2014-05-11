import sublime, sublime_plugin, re

SETTINGS_FILE = "PeopleCodeTools.sublime-settings"

class TidypctraceCommand(sublime_plugin.TextCommand):

    def replaceViewContent(self, viewToReplace, replaceString):
        viewToReplaceAllTextRegion = sublime.Region(0, viewToReplace.size())
        viewToReplace.replace(self.edit, viewToReplaceAllTextRegion, replaceString)
        viewToReplace.sel().clear()

    def run(self, edit):
        settings = sublime.load_settings(SETTINGS_FILE)
        self.edit = edit

        # Grab the original view contents and store it in a new file
        originalView = self.view;
        originalViewString = originalView.substr(sublime.Region(0, originalView.size()))

        newView = originalView.window().new_file()
        newViewString = originalViewString

        # Get location of syntax file
        originalSyntax = originalView.settings().get('syntax')

        ## Remove header junk
        if settings.get("tidy_remove_psappsrv_headers") == True:

            newViewString = re.sub(r'(?m)(^PSAPPSRV.*?\d\.\d{6}\s)(.*)', '\\2', newViewString)
            newViewString = re.sub(r'(?m)(^PSAPPSRV.*@JavaClient.*IntegrationSvc\]\(\d\)\s{3})(.*)', '\\2', newViewString)

        ## Fix up unmatched quotes
        ## Note: 4 regex replaces still seems to be more efficient than adding a quote to lines with an odd number of quotes
        if settings.get("tidy_add_unmatched_quotes") == True:
            newViewString = re.sub(r'(?m)(.*"[^";\)\s>]+$)', '\\1" - quote added by Tidy', newViewString)
            newViewString = re.sub(r'(?m)(.*\("[^"\n]+$)', '\\1" - quote added by Tidy', newViewString)
            newViewString = re.sub(r'(?m)(.*=")$', '\\1" - quote added by Tidy', newViewString)
            newViewString = re.sub(r'(?m)(.*class="[^"\n]+)$', '\\1" - quote added by Tidy', newViewString)

        ## Remove all blank spaces
        if settings.get("tidy_remove_blank_spaces") == True:
            newViewString = re.sub(r'(?m)^\n', '', newViewString)

        self.replaceViewContent(newView, newViewString)

        # Set syntax of new file and clear original selection
        newView.set_syntax_file(originalSyntax)
        newView.sel().clear()
