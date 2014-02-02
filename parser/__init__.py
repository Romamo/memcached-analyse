# -*- coding: utf-8 -*-

import datetime
import fileinput
import json
import re
import sys

class Parser(object):
    settings = None
    options = None
    # Статистика ключей
    keys = {}
    # Статистика групп ключей
    groups = {}

    dump =False

    # Статистика
    stats = {'keys_ungroupped': 0}

    def __init__(self, settings, options):
        self.settings = settings
        self.options = options

    def add(self, db, op, item, size=0, group=False, is_new=False):
        """
        Добавляет запись в db (keys или groups)
        Добавление ключа: self.keys, op, item, size, group
        Добавление группы: self.groups, op, item, size, is_new

        """
#        print "ADD\t", op, item, group, size

        if db.get(item, False) is False:
            if group is not False:
                db[item] = [0, 0, 0, group, 0]
            else:
                db[item] = [0, 0, 0, 0, 0]
        if op == 'hit':
            db[item][0] += 1
        elif op == 'miss':
            db[item][1] += 1
        elif op == 'set':
            db[item][2] += 1
            db[item][4] += size
        if is_new:
            db[item][3] += 1

    def key_group(self, key):
        """
        Парсит название ключа
        """
        for p in self.settings.PATTERN_GROUP:
            if re.search(p, key):
                return p
        for p in self.settings.PATTERN_KEY:
            group = re.sub(p, '%', key)
            if key != group:
                return group
        return None

    def key_add(self, op, key, size=0):
        """
        Добавляет ключ
        Парсит ключ, пытаясь выделить группу
        """
#        if key == '::g6':
#            print "KEY", op, key, size
        kdata = self.keys.get(key, None)
        if kdata is None:
            is_new = True
            group = self.key_group(key)
            if group is None:
                self.stats['keys_ungroupped'] += 1
            if self.options['print_keys']:
                if group is None:
                    print "* %s" % key
                else:
                    print "%20s <= %s" % (group, key)
        else:
            group = kdata[3]
            is_new = False
            if key == '::g6' and kdata[1] > 5:
                self.dump = True
        self.add(self.keys, op, key, size+len(key), group=group)
        self.add(self.groups, op, group, size+len(key), is_new=is_new)

#        if not added:
#            self.add(op, key, self.settings.NOGROUP, size)
#            # Еще раз для ключа добавляют статистику в группу nogroup
#
#            if key_new:
#                self.stats['keys_ungroupped'] += 1
#                if self.options['print_ungroupped']:
#                    print 'Ungroupped', key

    def parse_get(self, command):
#        print command
        keys = command[0][1:]
        answers = {}
        for answer in command[1]:
            if answer[0] == 'END':
                break
            if answer[0] == 'sending':
                answers[answer[2]] = True
        for key in keys:
            if answers.get(key, False):
                result = 'hit'
            else:
                result = 'miss'
            self.key_add(result, key)

    def parse_set(self, command):
#        print command
        self.key_add('set', command[0][1], int(command[0][-1]))

    def parse_command(self, command):
        if command[0][0] == 'get':
            return self.parse_get(command)
        if command[0][0] == 'set':
            return self.parse_set(command)

    def parse(self, input_file, limit_lines):
        """
        Parses dump file and extracts

        groupdump[name] = {(count, size)}

        grouplog[name] = {[hit, miss, set, unique_keys, size]}
        """
        if self.options['print_progress']:
            tstart = datetime.datetime.now()
        r_p = None
        commands = {}
        command = [[], []]
        size = 0
        lines = 0
        files = input_file and (input_file,) or ()
        i = 0
        for line in fileinput.input(files=files):
            lines += 1
            i += 1
            line = line.strip("\r\n")
            if not line:
                continue
            typ = line[0]
            if typ not in ['>','<']:
                continue
            r = line.decode('utf-8', errors='ignore').split(' ')
            thread = r[0][1:]

            if self.dump:
                print r
            if typ == '<':
                if len(r) < 2:
                    continue
                if r[1] in ['get', 'set']:
                    if commands.get(thread, None) is None:
                        commands[thread] = [[], []]
                    else:
                        if commands[thread][0]:
                            self.parse_command(commands[thread])
                            if self.dump:
                                print commands[thread]
                            commands[thread] = [[], []]
                    commands[thread][0] = r[1:]
            if typ == '>' and len(r) > 1:
                if commands.get(thread, None) is None:
                    commands[thread] = [[], []]
                commands[thread][1].append(r[1:])

            if self.options['print_progress'] and i >= 10000:
                sys.stdout.write("\rProcessed lines: %d Keys: %d" % (lines, len(self.keys)))
                sys.stdout.flush()
                i = 0
                if limit_lines and lines >= limit_lines:
                    break
        if self.options['print_progress']:
            tsec = (datetime.datetime.now() - tstart).seconds
            if not tsec:
                tsec = 1
            print "\nElapsed %s lines in %s seconds, %sM lines per sec" % (lines, tsec, lines/1024/1024/tsec)

    def totals(self):
        totals = {
           'name': 'Totals',
           'hit': 0,
           'miss': 0,
           'set': 0,
           'hitp': 0,
           'keys': 0,
           'size': 0,
           'sizep': 0,
           'mem': 100,
           }
        for g in self.keys:
            totals['hit'] += self.keys[g][0]
            totals['miss'] += self.keys[g][1]
            totals['set'] += self.keys[g][2]
            totals['keys'] += 1
            totals['size'] += self.keys[g][4]
        totals['hitp'] = totals['hit'] * 100 / (totals['hit'] + totals['miss'])
        return totals

    def count(self, db):
        data = []
        for g in db:
            data.append({
                       'name': g,
                       'hit': db[g][0],
                       'miss': db[g][1],
                       'set': db[g][2],
                       'hitp': db[g][0]*100/(db[g][0]+db[g][1]+db[g][2]),
                       'keys': db[g][3],
                       'size': db[g][4],
            })
        return data

    def get_data(self):
        if not len(self.keys):
            return None
        return (self.stats, self.totals(), self.count(self.keys), self.count(self.groups))

    def save_data(self, file):
        data = self.get_data()
        with open(file, 'w') as f:
            json.dump(data, f)

        with open(file, 'r') as f:
            json.load(f)
