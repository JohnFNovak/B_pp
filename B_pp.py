#!/usr/bin/python

# B Preprocessor
# John F. Novak
# Friday,  May 17,  2013,  12:48

# This processes *.B files into *.cpp files

import sys
import os
import re

newline = '\n'

Full = {}
Opts = {'@Passes': 5, '@Fdelimeter': '%', '@Levelindicator': '!',
        '@Verbose': '0'}


def Process(filename):
    oFull = open(filename, 'r').read()
    if (oFull[0] != '@') or (len(oFull.split(newline)) <= 3):
        print "file", filename, "does not appear to be properly formated"

    oFull = ProcessTemplate(oFull)

    #TEMPLATE = Full.split('@@')[2].split(newline)[1:]
    #ITERABLES = Full.split('@@')[3].split(newline)[1:]
    #FORMS = Full.split('@@')[4].split(newline)[1:]
    #REFERENCES = Full.split('@@')[5].split(newline)[1:]

    for i in range(Opts['@Passes'], -1, -1):
        pf = Opts['@Levelindicator'] * i
        if Opts['@Verbose'] >= 1:
            print "#=============#"
            print 'reading priority', Opts['@Passes'] - i + 1, "Flag: '%s'" % (pf)
        # First we expand the files
        for j in range(Opts['@Passes'], -1, -1):
            pf2 = Opts['@Levelindicator'] * j
            Full['TEMPLATE'] = ExpandFiles(Full['TEMPLATE'], i)
            Full[pf2 + 'ITERABLES'] = ExpandFiles(Full[pf2 + 'ITERABLES'], i)
            Full[pf2 + 'REFERENCES'] = ExpandFiles(Full[pf2 + 'REFERENCES'], i)

        # After loading files we reprocess the template, which allows you to
        # put new definitions in the files you reference
        oFull = ProcessTemplate(oFull)

        # First we have to load the ITERABLES
        IterDict = LoadIters(Full[pf + 'ITERABLES'])

        # Then we processes ITERABLES
        for j in range(Opts['@Passes'], -1, -1):
            pf2 = Opts['@Levelindicator'] * j
            Full['TEMPLATE'] = ExpandIters(Full['TEMPLATE'], IterDict, i)
            Full[pf2 + 'FORMS'] = ExpandIters(Full[pf2 + 'FORMS'], IterDict, i)
            Full[pf2 + 'REFERENCES'] = ExpandIters(Full[pf2 + 'REFERENCES'],
                                                   IterDict, i)

        # Then we handle FORMS

        # Then we load REFERENCES
        RefDict = LoadRefs(Full[pf + 'REFERENCES'])

        # Then we replace REFERENCES
        for j in range(Opts['@Passes'], -1, -1):
            pf2 = Opts['@Levelindicator'] * j
            Full['TEMPLATE'] = ExpandRefs(Full['TEMPLATE'], RefDict, i)
            Full[pf2 + 'ITERABLES'] = ExpandRefs(Full[pf2 + 'ITERABLES'],
                                                 RefDict, i)
            Full[pf2 + 'REFERENCES'] = ExpandRefs(Full[pf2 + 'REFERENCES'],
                                                  RefDict, i)

    output = open(filename.replace('.B', ''), 'w')
    output.write('\n'.join(Full['TEMPLATE']))
    output.close()


def ProcessTemplate(oFull):
    for i in oFull.split('@@'):
        options = None
        if i[:5] == 'GUIDE':
            print 'Loading options from the GUIDE:'
            options = i.split(newline)[1:-2]
        if options:
            for i in options:
                print i
                Opts[i.split(' = ')[0]] = i.split(' = ')[1]
    Opts['@Passes'] = int(Opts['@Passes']) - 1
    Opts['@Verbose'] = int(Opts['@Verbose'])

    if Opts['@Verbose'] >= 1:
        print "Levelindicator:", Opts['@Levelindicator']

    Full = {}

    Full['TEMPLATE'] = ''
    for i in range(Opts['@Passes'], -1, -1):
        pf = Opts['@Levelindicator'] * i
        Full[pf + 'ITERABLES'] = ''
        Full[pf + 'REFERENCES'] = ''
        Full[pf + 'FORMS'] = ''

    if Opts['@Verbose'] == 4:
        print Full
        print oFull

    for i in oFull.split('@@')[1:]:
        Full[i.split(newline)[0]] = i.split(newline)[1:-1]
        if Opts['@Verbose'] == 3:
            print i.split(newline)[0]
            print '---------------'
            print i.split(newline)[1:-1]
    if 'GUIDE' in Full.keys():
        del Full['GUIDE']

    oFull = newline.join([newline.join(['@@' + i] + [x for x in Full[i]]) for i in Full.keys()])

    if Opts['@Verbose'] == 4:
        print Full
        print oFull

    return oFull


def ExpandFiles(TEMPLATE, depth):
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
    ITERABLES = '\n'.join(ITERABLES)
    ITERABLES = ITERABLES.split('@')[1:]
    IDict = {}
    for i in ITERABLES:
        j = i.split('\n')[:-1]
        if len(j[0].split('(')[1][:-2].split(',')) == 1:
            IDict[j[0].split('(')[0]] = [j[0].split('(')[1][:-2].split(
                                         ','), map(lambda x: [x], j[1:])]
        else:
            IDict[j[0].split('(')[0]] = [j[0].split('(')[1][:-2].split(
                                         ','), map(lambda x: x.split(' '),
                                         j[1:])]
    if Opts['@Verbose'] >= 1:
        print 'Iters:', IDict.keys()
    return IDict


def ExpandIters(Text, Iters, depth):
    pf = Opts['@Levelindicator'] * depth
    #Text = '\n'.join(Text)
    good = False
    while not good:
        good = True
        cText = Text
        for line in Text:  # for every line
            for i in Iters:  # for every iter
                #print i
                if pf + '@' + i in line:
                    good = False
                    count = 0
                    for j in range(len(Iters[i][1])):  # for every iteration
                        # we seem to be getting an empty line sometimes...
                        if Iters[i][1][j][0]:
                            nline = line
                            if Opts['@Verbose'] >= 2:
                                print 'Replacing', line
                            #print line, j, Iters[i][1][j]
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
    REFERENCES = '\n'.join(REFERENCES)
    REFERENCES = REFERENCES.split('@')[1:]
    Refs = {}
    for i in REFERENCES:
        j = i.split('\n')
        if j[-1] == '':
            j = j[:-1]
        Refs[j[0][:-1]] = '\n'.join(j[1:])
    if Opts['@Verbose'] >= 1:
        print "Refs:", Refs
    return Refs


def ExpandRefs(Text, Refs, depth):
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

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for i in sys.argv[1:]:
            Process(i)
