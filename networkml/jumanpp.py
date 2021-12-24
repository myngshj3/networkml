# coding: utf-8
# It is not necessary when you use python3.
from __future__ import unicode_literals

import sys
import os
import networkml.genericutils as GU
from networkml.generic import debug, is_debug_mode, set_debug
from pyknp.juman.juman import Juman
from networkml.generic import debug, set_debug, is_debug_mode, GenericValueHolder
from networkml import config as LOG
import log4p
log = None  # logger.logger


class Jumanpp:

    def __init__(self, config_file=None):
        self._config = GU.read_json(config_file)
        global log
        logger = log4p.GetLogger(logger_name=__name__, config=LOG.get_log_config())
        log = logger.logger
        self._jumanpp = None
        self.setup()

    def setup(self):
        if self._jumanpp is None:
            cmd = self._config["command"]
            env = os.environ
            path = self._config["path"]
            env["PATH"] = "{};{}".format(path, env["PATH"])
            option = ""
            for k in self._config.keys():
                if k != "command" and k != "path" and k != "log-config":
                    if option == "":
                        option = "{} {}".format(k, self._config[k])
                    else:
                        option = "{} {} {}".format(option, k, self._config[k])
            print("command='{}', option='{}'".format(cmd, option))
            self._jumanpp = Juman(command=cmd, option=option)

    def __call__(self, *args, **kwargs):
        return self.parse(args[0])

    def parse(self, string):
        # print("begin parsing...")
        result = self._jumanpp.analysis(string)
        rtn = ""
        for i, mrph in enumerate(result.mrph_list()):  # 各形態素にアクセス
            log.info("\n{}{}".format(i+1, "-th morph,"))
            rtn = "{}\n見出し:{}, 読み:{}, 原形:{}, 品詞:{}, 品詞細分類:{}, 活用型:{}, 活用形:{}, 意味情報:{}, 代表表記:{}" \
                  .format(rtn, mrph.midasi, mrph.yomi, mrph.genkei, mrph.hinsi, mrph.bunrui, mrph.katuyou1,
                          mrph.katuyou2, mrph.imis, mrph.repname)
        # print("end parsing...")
        return rtn

    def try_parse(self, string):
        try:
            ret = self.parse(string)
            return ret
        except Exception as ex:
            print(ex)
            debug(ex)
            return Exception("Jumanpp error", ex)

