# -*- coding: utf-8 -*-

import json

class Reports(object):
    stats = None
    totals = None
    keys = None
    groups = None
    settings = None
    options = None

    head = {
           'name': '%s',
           'hit': 'Hits',
           'miss': 'Misses',
           'set': 'Sets',
           'hitp': 'Hitrate,%',
           'keys': 'Keys',
           'sizep': 'Size',
           'mem': 'Mem,%',
                }
    align = "%(name)60s%(hit)10s%(miss)10s%(set)10s%(hitp)10s%(keys)10s%(sizep)10s%(mem)10s"

    allowed_reports = ['hit', 'keys', 'hitp', 'miss', 'set', 'size']

    def __init__(self, settings, options, data):
        self.settings = settings
        self.options = options
        if not data:
            print 'No data'
            return
        elif type(data) == str:
            with open(data, 'r') as f:
                data = json.load(f)

        (self.stats, self.totals, self.keys, self.groups) = data
        self.totals['sizep'] = self.print_size(self.totals['size'])

    def print_stats(self):
        print "Keys total: %s, ungrupped: %s (%s%%)" % (len(self.keys), self.stats['keys_ungroupped'], self.stats['keys_ungroupped']*100 / len(self.keys))
        print "Total groups:", len(self.groups)
        self.print_head('t')
        self.print_totals()

    def print_totals(self):
        print self.align % self.totals

    def prepare_reports(self, reports):
        """
        Формирует конфиг репортов
        """
        config = []

        for r in reports.split(','):
            l = r.split(':')
            if l[0] in ['k', 'g'] and l[1] in self.allowed_reports:
                config.append((l[0], l[1], int(l[2])))
        return config

    def print_report(self, config):
        """
        Выводит отчет
        """
        (what, sort, limit) = config
        if self.options['groups'] and what != 'k':
            return
        if limit < 0:
            reversed = False
            limit = abs(limit)
        else:
            reversed = True

        if reversed:
            print "Top %s %s" % (limit, sort)
        else:
            print "Bottom %s %s" % (limit, sort)
        self.print_head(what)
        self.print_top(what, sort, reversed, limit)
        print

    def print_head(self, what):
        title = {'k': 'Key', 'g': 'Group', 't': 'Totals'}
        self.head['name'] = title[what]
        print self.align % self.head

    def print_top(self, what, sort, sort_reverse, limit):
        if what == 'k':
            data = self.keys
        else:
            data = self.groups
        i = 0
        for g in sorted(data, key=lambda d: d[sort], reverse=sort_reverse):
            if what == 'k' and self.options['groups'] and g['keys'] not in self.options['groups']:
                continue
            if g.get('sizep', None) is None:
                g['sizep'] = self.print_size(g['size'])
            if g.get('mem', None) is None:
                g['mem'] = g['size']*100/self.totals['size']
            print self.align % g
            i += 1
            if i > limit:
                break

    def print_size(self, size):
        if size > 1024*1024:
            return str(size/1024/1024) + 'm'
        if size > 1024:
            return str(size/1024) + 'k'
        return size

    def print_divide(self, a, b):
        if not b:
            return 0
        return a / b

    def main(self, reports=None):
        if not self.keys:
            print "No keys"
            return
        if reports:
            config = self.prepare_reports(reports)
            if not config:
                config = self.settings.REPORTS_DEFAULT
        else:
            config = self.settings.REPORTS_DEFAULT

        self.print_stats()

        for c in config:
            self.print_report(c)
