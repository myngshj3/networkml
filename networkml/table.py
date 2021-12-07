# -*- coding: utf-8 -*-

import re


class Table:

    def __init__(self, data):
        self._data = data
        self._columns = {}
        self.prepare()

    def prepare(self):
        header = self._data[0]
        for i, c in enumerate(header):
            self._columns[c] = i
        self._data = [_ for _ in self._data[1:]]
        pass

    @property
    def rows(self):
        return len(self._columns)

    @property
    def columns(self):
        return len(self._columns.keys())

    def sort(self, orders=()):
        pass

    def select(self, cols=(), predicates=None, orders=()):
        table = []
        r = []
        for c in cols:
            r.append(c)
        table.append(tuple(r))
        for row in self._data:
            r = []
            for c in cols:
                r.append(row[self._columns[c]])
            r = tuple(r)
            table.append(r)
        table = Table(table)
        table.sort(orders)
        return table

    def select_row(self, index):
        return self._data[index]

    def rawdata(self):
        data = []
        r = []
        for c in self._columns.keys():
            r.append(c)
        data.append(tuple(r))
        for row in self._data:
            r = []
            for c in self._columns.keys():
                r.append(row[self._columns[c]])
            data.append(tuple(r))
        return data
