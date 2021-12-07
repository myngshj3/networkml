# -*- coding: utf-8 -*-

import ply.lex as lex
import ply.yacc as yacc
import re
import sys
import traceback
import nltk

# import our modules


def print_all_leaves(tree: nltk.tree.Tree):
    print(tree)


def interpret(tree: nltk.tree.Tree):
    print_all_leaves(tree)
