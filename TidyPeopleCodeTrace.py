import sublime, sublime_plugin
import PeopleCodeTools.regex

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
        

