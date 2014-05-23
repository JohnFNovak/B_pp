#!/usr/bin/python

# B Preprocessor
# John F. Novak
# Friday,  May 17,  2013,  12:48

# This processes *.B files into *.cpp files

import sys
import os
import re
import code
import subprocess

newline = '\n'

global Opts
Opts = {'@Passes': 5, '@Fdelimeter': '%', '@Levelindicator': '!',
        '@Verbose': 0}


def Process(filename, Full=None):
    global Opts
    if not Full:
        if not FormatTest(filename):
            return False
        oFull = getFile(filename)
        if not oFull:
            return False
        Full = ProcessTemplate(text=oFull)

    while Opts['@Passes'] > -1:
        pf = Opts['@Levelindicator'] * Opts['@Passes']
        if Opts['@Verbose'] >= 1:
            print "#=============#"
            print 'reading priority', Opts['@Passes'] - Opts['@Passes'] + 1,
            print "Flag: '%s'" % (pf)
        # First we expand the files
        Full = DoFileExpansion(Full)

        # After loading files we reprocess the template, which allows you to
        # put new definitions in the files you reference
        Full = ProcessTemplate(dic=Full)

        # First we have to load the ITERABLES
        Full = DoIterExpansion(Full)

        # Then we load REFERENCES
        Full = DoRefExpansion(Full)

        Opts['@Passes'] = int(Opts['@Passes']) - 1

    with open(filename.replace('.B', ''), 'w') as output:
        output.write('\n'.join(Full['TEMPLATE']))

    return True


def ProcessInteractive(filename):
    global Opts
    print "Interactively processing", filename
    if not FormatTest(filename):
        print 'Failed format test'
        return False
    oFull = getFile(filename)
    if not oFull:
        print 'getFile failed'
        return False
    Full = ProcessTemplate(text=oFull)

    command = True
    step = 0
    history = []
    while command:
        print '#=====================#'
        print '[%s]' % (Opts['@Levelindicator'] * Opts['@Passes']),
        command = raw_input('(f,p,i,r,?): ') or '.'
        history.append(command)
        if command == 'x':
            Examine(Full, oFull)
        elif command == 'f':
            print "Performing (f)ile expansion"
            Full = DoFileExpansion(Full)
        elif command == 'i':
            print "Performing (i)terables expansion"
            Full = DoIterExpansion(Full)
        elif command == 'r':
            print "Performing (r)eferences expansion"
            Full = DoRefExpansion(Full)
        elif command == 'p':
            print "Re(p)rocessing template"
            Full = ProcessTemplate(dic=Full)
        elif command == '?':
            PrintHelp()
        elif command == 's':
            print "(s)tepping down a level. @Passes =", Opts['@Passes'], "->",
            Opts['@Passes'] = int(Opts['@Passes']) - 1
            print Opts['@Passes']
        elif command == '!':
            interact(Full=Full)
        elif command == 'g':
            print "(g)o: Proceeding with non-interactive processing"
            return Process(filename, Full=Full)
        elif command == 'q':
            return True
        elif command == 'w':
            print "(w)riting out file"
            newname = filename.replace('.B', '')
            newname = raw_input('write to [%s]: ' %
                                (newname)).strip() or newname
            with open(newname.replace('.B', ''), 'w') as output:
                output.write('\n'.join(Full['TEMPLATE']))
        elif command == 'v':
            v = raw_input('set verbose to (int, 0-5): ').strip()
            try:
                v = int(v)
                if v >= 0 and v <= 5:
                    Opts['@Verbose'] = v
            except ValueError:
                print "input returned TypeError, command ignored"
        elif command == 'h':
            print "History:"
            print history
        elif command == 'e':
            with open('.temp', 'w') as f:
                f.write(to_text(Full))
            subprocess.call(('vim', '.temp'))
            with open('.temp', 'r') as f:
                Full = ProcessTemplate(f.read())
            os.remove('.temp')
        elif command == '.':
            if step == 0:
                print "Performing file expansion"
                Full = DoFileExpansion(Full)
            elif step == 1:
                print "Reprocessing template"
                Full = ProcessTemplate(dic=Full)
            elif step == 2:
                print "Performing iterables expansion"
                Full = DoIterExpansion(Full)
            elif step == 3:
                print "Performing references expansion"
                Full = DoRefExpansion(Full)
                print "Stepping down a level. @Passes =", Opts['@Passes'],
                Opts['@Passes'] = int(Opts['@Passes']) - 1
                print "->", Opts['@Passes']
            if Opts['@Passes'] < 0:
                print "Writing out file to", filename.replace('.B', '')
                with open(filename.replace('.B', ''), 'w') as output:
                    output.write('\n'.join(Full['TEMPLATE']))
                return True
            step += 1
            step %= 4
        else:
            print "Command not recognized"

    with open(filename.replace('.B', ''), 'w') as output:
        output.write('\n'.join(Full['TEMPLATE']))


def Examine(Full, oFull):
    global Opts
    print '#===============#'
    print 'oFull:'
    print oFull
    print '#===============#'
    print 'Full:'
    print Full
    print '#===============#'
    print 'Opts:'
    print Opts
    print '#===============#'


def PrintHelp():
    print """Here are the available options:
    x: Examine(), prints out certain values
    f: performs file expansion
    i: performs iterable expansion
    r: performs reference expansion
    p: processes the current full template
    s: steps down a pass. ie: Opts[\'@Passes\'] -= 1
    !: drops to an interactive shell
    g: runs non-interactive file expansion
    v: allows you to change the verbosity of the output
    h: prints out the recent command history
    w: writes the current file to disk
    q: exit"""


def getFile(filename):
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            oFull = f.read()
    else:
        print filename, "does not appear to be a file"
        return False
    return oFull


def FormatTest(filename):
    global Opts
    text = getFile(filename)
    Valid = True

    key = ['OTHER', 0]
    breaks = []
    depth = 0
    for l, i in enumerate(text.split('\n')):
        trimmed = i.split('#')[0].strip()
        if len(trimmed) > 2 and trimmed[:2] == '@@':
            if depth == 0:
                key[0] = trimmed[2:].split(':')[0]
                key[1] = l
            depth += 1
            breaks.append([trimmed, trimmed[2:], l, depth])
        elif len(trimmed) > 2 and trimmed[-2:] == '@@':
            depth -= 1
            if trimmed[:-2] == key and depth == 0:
                key[0] = 'OTHER'
                key[1] = l
            # if i[:-2] != key:
            #     print 'Unmatched closed tag found:', i, 'in', key[0], 'block',
            #     print 'started on line', key[1]
            breaks.append([trimmed, trimmed[:-2], l, depth])
            depth -= 1

    breaks.sort(reverse=True, key=lambda x: [x[-1], -x[-2]])
    while len(breaks) > 1:
        breaks.sort(key=lambda x: [x[-1], -x[-2]])
        key = breaks.pop()
        if breaks[-1][1] == key[1]:
            # This is what should happen, the next break is the exit
            del(breaks[-1])
        else:
            if Valid:
                print 'file:', filename, 'is not properly formated'
            Valid = False
            if depth > 0:
                print key[1], 'block not properly closed. Opened line', key[2]
                # breaks.sort(reverse=True, key=lambda x: [x[-1], -x[-2]])
                # for i in breaks:
                #     print i
                # print 'updating depths?'
                breaks = [x[:3] + [x[3] - 1] if x[2] > key[2]
                          else x for x in breaks]
                depth -= 1
                # breaks.sort(reverse=True, key=lambda x: [x[-1], -x[-2]])
                # for i in breaks:
                #     print i
            elif depth < 0:
                if key[1] + '@@' in [x[0] for x in breaks]:
                    # The exit break exists, but there is other stuff too
                    i = len(breaks) - [x[0] for x in
                                       breaks][-1::-1].index(key[1] + '@@') - 1
                    # print 'Matching break found for', key[1],
                    # print 'index', i - len(breaks)
                    # print breaks[i - len(breaks)]
                    for index, j in enumerate(breaks[i - len(breaks) + 1:]):
                        # print "\t", i - len(breaks) + index + 1, ',', j
                        print 'Extra', j[1], 'close tag found on line', j[2],
                        print 'in', key[1], 'block opened on line', key[2]
                        depth += 1
                    del(breaks[i - len(breaks) + 2:])
                else:
                    # The exit break does not exsit
                    print 'Error:', key[1], 'block not closed. Opened line',
                    print key[2]
                # sys.exit(1)

    if depth > 0:
        if Valid:
            print 'file:', filename, 'is not properly formated'
        print breaks[0][1], 'block not properly closed. Opened line',
        print breaks[0][2]
        Valid = False

    return Valid


def to_text(Full):
    text = newline.join([newline.join(['@@' + i] +
                         [x for x in Full[i]] +
                         [i + '@@']) if i != 'OTHER' else newline.join(Full[i])
                        for i in Full.keys()])
    return text


def ProcessTemplate(text=None, dic=None):
    global Opts
    options = None

    # Full is only empty on the first pass, so we make it
    if dic:  # If it is not the first pass, we need to remake text first
        text = to_text(dic)
    elif not text:
        print "No values passed to function: ProcessTemplate"
        return False
    dic = {}

    if Opts['@Verbose'] == 4:
        print 'ProcessTemplate: before parsing the text'
        print 'dic:', dic
        print 'text:'
        print text

    key = 'OTHER'
    depth = 0
    for i in text.split('\n'):
        trimmed = i.split('#')[0].strip()
        if len(trimmed) > 2 and trimmed[:2] == '@@':
            if depth == 0:
                key = trimmed[2:].split(':')[0]
            depth += 1
        elif len(trimmed) > 2 and trimmed[-2:] == '@@':
            depth -= 1
            if trimmed[:-2] == key and depth == 0:
                key = 'OTHER'
        else:
            if key in dic:
                dic[key].append(i)
            else:
                dic[key] = [i]

    if Opts['@Verbose'] == 4:
        print 'ProcessTemplate: after parsing the text'
        print 'dic:', dic
        print 'text:'
        print text

    if 'GUIDE' in dic:
        dic['GUIDE'] = [x for x in dic['GUIDE'] if x.split('#')[0].strip()]
        options = dic['GUIDE']
    if options:
        if int(Opts['@Verbose']) > 1:
            print 'Loading options from the GUIDE:'
        for i in options:
            Opts[i.split('=')[0].strip()] = i.split('=')[1].strip()
            if int(Opts['@Verbose']) > 1:
                print i.split('=')[0].strip(), '=',
                print Opts[i.split('=')[0].strip()]
        if int(Opts['@Verbose']) > 1:
            print "Levelindicator:", Opts['@Levelindicator']
        Opts['@Passes'] = int(Opts['@Passes']) - 1
    Opts['@Verbose'] = int(Opts['@Verbose'])

    if Opts['@Verbose'] == 3:
        print 'ProcessTemplate: before building the dictionary'
        for i in dic:
            print i
            print dic[i]
    if 'GUIDE' in dic.keys():
        del dic['GUIDE']

    dic = {key: ([x for x in dic[key] if x.split('#')[0].strip()] if key !=
           'TEMPLATE' else dic[key]) for key in dic.keys()}

    text = to_text(dic)

    if Opts['@Verbose'] == 3:
        print 'ProcessTemplate: after building the dictionary'
        for i in dic:
            print i
            print dic[i]
    if Opts['@Verbose'] == 4:
        print 'ProcessTemplate: after building the dictionary'
        print 'dic:', dic
        print 'text:'
        print text

    if not 'TEMPLATE' in dic:
        print 'KeyError: \'TEMPLATE\' not found in Full'
        if raw_input('enter interactive shell? (y/n): ').lower()[0] == 'y':
            interact(**{'Full': dic, 'text': text})

    return dic


def ExpandFiles(TEMPLATE, depth):
    global Opts
    FD = Opts['@Fdelimeter']
    pf = Opts['@Levelindicator'] * depth
    files_expanded = False
    while not files_expanded:
        files_expanded = True
        nTEMPLATE = TEMPLATE
        for line in TEMPLATE:
            if re.search(pf + FD + '([^' + FD + ']+)' + FD, line
                         ) and not 'printf' in line:
                files_expanded = False
                SubFile = re.search(pf + FD + '([^' + FD + ']+)' + FD, line)
                if Opts['@Verbose'] >= 1:
                    print 'File:', SubFile.group(1).split('[')[0]
                if SubFile.group:
                    oSubFile = SubFile.group()
                    #print oSubFile
                    SubFile = SubFile.group(1)
                    if os.path.isfile(SubFile.split('[')[0]):
                        if SubFile[-1] == ']':
                            SubRange = SubFile[:-1].split('[')[1]
                            SubFile = SubFile.split('[')[0]
                            if SubRange.count(',') == 0:
                                adding = [open(SubFile, 'r').read().split(
                                          newline)[int(SubRange)]]
                            if SubRange.count(',') == 1:
                                SubRange = SubRange.split(',')
                                if SubRange[0] == ':':
                                    adding = open(SubFile, 'r').read().split(
                                        newline)[:int(SubRange[1])]
                                elif SubRange[1] == ':':
                                    adding = open(SubFile, 'r').read().split(
                                        newline)[int(SubRange[0]):-1]
                                else:
                                    adding = open(SubFile, 'r').read().split(
                                        newline)[int(SubRange[0]):int(
                                        SubRange[1])]
                            if SubRange.count(',') == 2:
                                SubRange = SubRange.split(',')
                                if SubRange[0] == ':':
                                    adding = open(SubFile, 'r').read().split(
                                        newline)[:int(SubRange[1])]
                                elif SubRange[1] == ':':
                                    adding = open(SubFile, 'r').read().split(
                                        newline)[int(SubRange[0]):-1]
                                else:
                                    adding = open(SubFile, 'r').read().split(
                                        newline)[int(SubRange[0]):int(
                                        SubRange[1])]
                                temp = []
                                for i in range(len(adding)):
                                    if i % int(SubRange[2]) == 0:
                                        temp.append(adding[i])
                                adding = temp
                        else:
                            adding = open(SubFile, 'r').read().split(
                                newline)
                            if adding[-1] == '':
                                adding = adding[:-1]
                        count = 0
                        #print line
                        for nline in adding:
                            #print nline
                            nTEMPLATE.insert(TEMPLATE.index(line) + count,
                                             line.replace(oSubFile, nline))
                            count += 1
                        del nTEMPLATE[TEMPLATE.index(line)]
                        break
                    else:
                        print 'Error in line:', line
                        print SubFile.split('[')[0],
                        print 'does not seem to be a file'
                        exit(1)
        TEMPLATE = nTEMPLATE
    return TEMPLATE


def LoadIters(ITERABLES):
    global Opts
    ITERABLES = '\n'.join(ITERABLES)
    ITERABLES = ITERABLES.split('@')[1:]
    IDict = {}
    for i in ITERABLES:
        j = [x for x in [y.split('#')[0].strip() for y in i.split('\n')] if x]
        if len(j[0].split('(')[1][:-2].split(',')) == 1:
            IDict[j[0].split('(')[0]] = [j[0].split('(')[1][:-2].split(
                                         ','), map(lambda x: [x], j[1:])]
        else:
            IDict[j[0].split('(')[0]] = [j[0].split('(')[1][:-2].split(
                                         ','), map(lambda x: x.split(' '),
                                         j[1:])]
    if Opts['@Verbose'] >= 1:
        print 'Iters:', IDict.keys()
        for i in IDict:
            print i, IDict[i]
    return IDict


def ExpandIters(Text, Iters, depth):
    global Opts
    pf = Opts['@Levelindicator'] * depth
    #Text = '\n'.join(Text)
    good = False
    while not good:
        good = True
        cText = Text
        for line in Text:  # for every line
            for i in Iters:  # for every iter
                # print i
                if pf + '@' + i.split('.')[0] + '.' in line:
                    good = False
                    count = 0
                    for j in range(len(Iters[i][1])):  # for every iteration
                        # we seem to be getting an empty line sometimes...
                        if Iters[i][1][j][0]:
                            nline = line
                            if Opts['@Verbose'] >= 2:
                                print 'Replacing', line
                            # print line, j, Iters[i][1][j]
                            nline = nline.replace(pf + '@i@', str(j))
                            # for every id in the key
                            for k in range(len(Iters[i][0])):
                                #print '@'+i+'.'+Iters[i][0][k]+'@'
                                nline = nline.replace(pf + '@' + i + '.' +
                                                      Iters[i][0][k] + '@',
                                                      str(Iters[i][1][j][k]))
                            cText.insert(Text.index(line) + count, nline)
                            count += 1
                            if Opts['@Verbose'] >= 2:
                                print 'Replaced:', nline
                            #print nline
                    del cText[Text.index(line)]
                    Text = cText
                    break
    #print Text
    return Text


def LoadRefs(REFERENCES):
    global Opts
    Refs = {}
    key = ''
    for i in REFERENCES:
        if i[0] == '@':
            key = i[1:].split(':')[0]
            Refs[key] = []
        elif key in Refs:
            Refs[key].append(i)
    Refs = {k: '\n'.join([x for x in [y.split('#')[0] for y in Refs[k]]
            if x.strip()]) for k in Refs}
    if Opts['@Verbose'] >= 1:
        print "Refs:", Refs
    return Refs


def ExpandRefs(Text, Refs, depth):
    global Opts
    pf = Opts['@Levelindicator'] * depth
    good = False
    while not good:
        good = True
        cText = Text
        for line in Text:  # for every line
            for i in Refs:  # for every iter
                if pf + '@' + i + '@' in line:
                    good = False
                    nline = line
                    nline = nline.replace(pf + '@' + i + '@', Refs[i])
                    cText.insert(Text.index(line), nline)
                    del cText[Text.index(line)]
                    Text = cText
                    break
    return Text


def DoFileExpansion(Full):
    global Opts
    for j in range(Opts['@Passes'], -1, -1):
        pf2 = Opts['@Levelindicator'] * j
        keys = ['TEMPLATE', 'OTHER', pf2 + 'ITERABLES', pf2 + 'REFERENCES']
        for k in keys:
            if k in Full:
                Full[k] = ExpandFiles(Full[k], Opts['@Passes'])
    return Full


def DoIterExpansion(Full):
    global Opts
    pf = Opts['@Levelindicator'] * Opts['@Passes']
    if pf + 'ITERABLES' in Full:
        IterDict = LoadIters(Full[pf + 'ITERABLES'])
        # Then we processes ITERABLES
        for j in range(Opts['@Passes'], -1, -1):
            pf2 = Opts['@Levelindicator'] * j
            keys = ['TEMPLATE', 'OTHER', pf2 + 'REFERENCES']
            for k in keys:
                if k in Full:
                    Full[k] = ExpandIters(Full[k], IterDict, Opts['@Passes'])
    return Full


def DoRefExpansion(Full):
    global Opts
    pf = Opts['@Levelindicator'] * Opts['@Passes']
    if pf + 'REFERENCES' in Full:
        RefDict = LoadRefs(Full[pf + 'REFERENCES'])
        # Then we replace REFERENCES
        for j in range(Opts['@Passes'], -1, -1):
            pf2 = Opts['@Levelindicator'] * j
            keys = ['TEMPLATE', 'OTHER', pf2 + 'ITERABLES']
            for k in keys:
                if k in Full:
                    Full[k] = ExpandRefs(Full[k], RefDict, Opts['@Passes'])
    return Full


def interact(**kwargs):
    global Opts
    code.InteractiveConsole(locals=dict(globals().items() +
                                        kwargs.items())).interact()
    return True


def PrintExample():
    print """@@GUIDE
# These are the default values
@Passes = 5
@Fdelimeter = %
@Levelindicator = !
@Verbose = 0
GUIDE@@

@@TEMPLATE
This is just an example
Comments can be included in templates. Any comment in the TEMPLATE block will
be preserved. Lines beginning with '#' will be ignored and anything after '#'
in a line will also be ignored.

This is an example of a @ref@.

This is an example of an iterable: @list.num@ and @list.letter@
TEMPLATE@@

@@ITERABLES
@list(num,letter):
1 a
2 b
3 c
ITERABLES@@

@@REFERENCES
@ref:
reference. References are string replacements
REFERENCES@@
    """


def main():
    Interactive = '-i' in sys.argv
    Test = '-t' in sys.argv
    if '-p' in sys.argv:
        PrintExample()
    if '-h' in [x[:2] for x in sys.argv] or '--help' in sys.argv:
        print """
the B Preprocessor

This is a template processor which is designed for preprocessing code templates
before being compiled. For details https://github.com/JohnFNovak/B_pp

usage: $ B <template1> <template2> <template3> ...

Compiling a template name template.B.ftype will compile to template.ftype

Flags:
    -i : the template processor will start in interactive mode. The processor
            will load into an interactive prompt. A python shell can be
            accessed via a '!' command at the prompt. '?' will print more help
    -t : the template processor will run in 'test' mode. Templates will not be
            compiled. Templates will only be checked for valid format. output
            will only be returned if errors are found. This is useful when
            batch testing the validity of templates.
    -p : prints an example template to standard out.

Format:
    For detailed information go to https://github.com/JohnFNovak/B_pp

    This abridged guide does not address order of operations, multiple level
        processing, nested templates, or the interactive mode. For information
        on that, please refer to the online references.

    Templates can contain four types of blocks: GUIDE, ITERABLES, and
        REFERENCES, TEMPLATE. Each block must begin with a line which says
        @@NAME and end with a line which says NAME@@ where NAME is one of the
        four types. In addition to the four block types, files can be included
        inline.

        File inclusion:
            Files are treated as strings. File representation is done as
                %<path_to_file/file.txt>%, where at compilation the contents of
                file.txt will loaded and %<path_to_file/file.txt>% will be
                replaced by the file contents. The '%' bookends are defaults,
                but any string can be used and is defined by the @Fdelimeter
                option in the GUIDE block (see next).

        GUIDE:
            The GUIDE block sets compilation options. Currently there are four.
            These are the current options and their defaults. To set them in a
            template they must we written @Name = <value> in the guide section.
                @Passes = 5
                @Fdelimeter = %
                @Levelindicator = !
                @Verbose = 0
        ITERABLES:
            Iterables are lists of sets of strings. In the iterables seciton
            iterables are defined as
                @Name(prop1, prop2, ...):
                thing1_prop1 thing1_prop2 ...
                thing2_prop1 thing2_prop2 ...
                ...
            Iterables can be arbitrarily long and can have arbitrarily many
                properties.
            When referenced in the TEMPLATE block an iterable is referenced as
                line in code blah_blah_blah @Name.propname@ continues with code
            The line will get copied once for each entry in the iterable, and
                the string @Name.propname@ will be replaced with the value
                from iterable Name, with property name propname.
            If an iterable is referenced more than one in a signle line, all of
                the instances will be replaced at the same time.

                ex:
                @List(num, letter):
                5 a
                6 b
                7 c

                Then the line:
                    Test line @List.num@ more filler @List.letter@
                Will compile to:
                    Test line 5 more filler a
                    Test line 6 more filler b
                    Test line 7 more filler c

            The special iterable @i@ will be replaced by the count of the
                iteration.
                With the previous example:
                    The line:
                        @i@ Test line @List.num@ more filler @List.letter@
                    Will compile to:
                        1 Test line 5 more filler a
                        2 Test line 6 more filler b
                        3 Test line 7 more filler c

        REFERENCES:
            Refernces are strings which are replaced at compilation. Refernces
            are defined in the REFERENCES block as:
                @Refname:
                string to replace
            Then, any instance of @Refname@ in the TEMPLATE block will compile
                to "string to replace"

            ex:
            @ref1:
            just an example

            Then the line:
                test line @ref1@ more filler
            Will compile to:
                test line just an example more filler

        TEMPLATE:
            The template block is the part of the template which is compiled
            into the final result. Refernces and iterables are expanded and the
            result is printed out to file.
        """
    if len(sys.argv) > 1:
        for i in [x for x in sys.argv[1:] if x[0] != '-']:
            if Test:
                FormatTest(i)
            else:
                if Interactive:
                    ProcessInteractive(i)
                else:
                    Process(i)
    else:
        print "No files given. -h or --help flag for help."

if __name__ == '__main__':
    main()
