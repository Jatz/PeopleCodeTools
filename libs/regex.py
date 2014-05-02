import sublime, sublime_plugin, re

def regex_extract(self, view, find):
    regions = view.sel()
    alltextreg = sublime.Region(0, view.size())
    callStackList = ''
    lines = view.lines(alltextreg)
    for line in lines:
        lineContents = view.substr(line)
        match = re.search(find, lineContents)
        if match:
            callStackList = callStackList + match.group() + '\n'
    view.replace(self.edit, alltextreg, callStackList)


def regex_findall(view, find, flags, replace, extractions, literal=False, sel=None):
    regions = []
    offset = 0
    if sel is not None:
        offset = sel.begin()
        bfr = view.substr(sublime.Region(offset, sel.end()))
    else:
        bfr = view.substr(sublime.Region(0, view.size()))
    flags |= re.MULTILINE
    if literal:
        find = re.escape(find)
    for m in re.compile(find, flags).finditer(bfr):
        regions.append(sublime.Region(offset + m.start(0), offset + m.end(0)))
        extractions.append(m.expand(replace))
    return regions

def greedy_replace(self, view, replace, regions):
    replaced = 0
    count = len(regions) - 1
    for region in reversed(regions):
        replaced += 1
        view.replace(self.edit, region, replace[count])
        count -= 1
    return replaced
