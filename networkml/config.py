# -*- coding: utf-8 -*-


_conf = None

def set_log_config(conf):
    global _conf
    _conf = conf


def get_log_config():
    global _conf
    return _conf
