# -*- coding: utf-8 -*-

import re
import sys
import re
import json
import xml.etree.ElementTree as ET


def rematch(pattern, target, groupdict=True):
    m = re.match(pattern, target)
    if m is None:
        return None
    if groupdict:
        return m, m.groupdict()
    return m


def re_match(pattern, target, groupdict=True):
    return rematch(pattern, target, groupdict)


def pattern_iter(pattern, target):
    m = re.match(pattern, target, re.MULTILINE)
    if m is None:
        return None, None, None
    return m, m.groupdict(), m.span()[1]


def read_xml(filename):
    tree = ET.parse(filename)
    return tree


def read_json(filename):
    with open(filename, "r") as f:
        # comment line supported
        p = r"^\s*(#.*|//.*|)$"
        lines = []
        for l in f.readlines():
            m = re.match(p, l)
            if m is None:
                lines.append(l)
            else:
                lines.append("\n")
        return json.loads("".join(lines))
