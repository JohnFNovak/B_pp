#!/usr/bin/python

# B Preprocessor
# John F. Novak
# Friday,  May 17,  2013,  12:48

# This processes *.B files into *.cpp files

import sys
import os
import re
import code

newline = '\n'

global Opts
Opts = {'@Passes': 5, '@Fdelimeter': '%', '@Levelindicator': '!',
        '@Verbose': 0}


def Process(filename, Full=None):
    global Opts
    if not Full:
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
    oFull = getFile(filename)
    if not oFull:
        return False
    Full = ProcessTemplate(text=oFull)

    command = True
    step = 0
    while command:
        command = raw_input('(x,f,i,r,p,?,s,!,g,q): ') or '.'
        if command == 'x':
            Examine(Full, oFull)
        if command == 'f':
            Full = DoFileExpansion(Full)
        if command == 'i':
            Full = DoIterExpansion(Full)
        if command == 'r':
            Full = DoRefExpansion(Full)
        if command == 'p':
            Full = ProcessTemplate(dic=Full)
        if command == '?':
            PrintHelp()
        if command == 's':
            Opts['@Passes'] = int(Opts['@Passes']) - 1
        if command == '!':
            interact(Full=Full)
        if command == 'g':
            return Process(filename, Full=Full)
        if command == 'q':
            return True
        if command == '.':
            if step == 0:
                Full = DoFileExpansion(Full)
            elif step == 1:
                Full = ProcessTemplate(dic=Full)
            elif step == 2:
                Full = DoIterExpansion(Full)
            elif step == 3:
                Full = DoRefExpansion(Full)
                Opts['@Passes'] = int(Opts['@Passes']) - 1
            if Opts['@Passes'] < 0:
                return True
            step += 1
            step %= 4

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
    print 'Here are the available options:'
    print 'x: Examine(), prints out certain values'
    print 'f: performs file expansion'
    print 'i: performs iterable expansion'
    print 'r: performs reference expansion'
    print 'p: processes the current full template'
    print 's: steps down a pass. ie: Opts[\'@Passes\'] -= 1'
    print '!: drops to an interactive shell'
    print 'g: runs non-interactive file expansion'
    print 'q: exit'


def getFile(filename):
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            oFull = f.read()
    else:
        print filename, "does not appear to be a file"
        return False
    if (oFull[0] != '@') or (len(oFull.split(newline)) <= 3):
        print "file", filename, "does not appear to be properly formated"
        return False
    return oFull


def ProcessTemplate(text=None, dic=None):
    global Opts
    options = None

    # Full is only empty on the first pass, so we make it
    if dic:  # If it is not the first pass, we need to remake text first
        text = newline.join([newline.join(['@@' + i] + [x for x in dic[i]] +
                            [i + '@@']) for i in dic.keys()])
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
        if len(i) > 2 and i[:2] == '@@':
            if depth == 0:
                key = i[2:].split(':')[0]
            depth += 1
        elif len(i) > 2 and i[-2:] == '@@':
            depth -= 1
            if i[:-2] == key and depth == 0:
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

    dic = {key: ([x for x in dic[key] if x.strip()] if key != 'TEMPLATE' else
           dic[key]) for key in dic.keys()}

    text = newline.join([newline.join(['@@' + i] + [x for x in dic[i]]) for i
                        in dic.keys()])

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
        j = [x for x in i.split('\n') if x.strip()]
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
    Refs = {k: '\n'.join([x for x in Refs[k] if x.strip()]) for k in Refs}
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


if __name__ == '__main__':
    Interactive = '-i' in sys.argv
    if len(sys.argv) > 1:
        for i in [x for x in sys.argv[1:] if x[0] != '-']:
            if Interactive:
                ProcessInteractive(i)
            else:
                Process(i)
