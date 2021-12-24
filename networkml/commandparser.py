# -*- coding:utf-8 -*-

import sys
import networkml.genericutils as GU


class CommandParser:

    def __init__(self, **patterns):
        self._pattern_config = patterns
        self._pattern = ""

    # def construct(self):
    #     pat = ""
    #     for i, p in sorted(self._pattern_config.keys()):
    #         seg = ""
    #         for k in p.keys():
    #             pass
    #
    # def find_token_sequence(self, script, tag):
    #     pattern = self._pattern_config[tag]
    #     token_sequence = []
    #     for pt in pattern:
    #         s = script
    #         token_list = [0]
    #         for i, p in enumerate(pt):
    #             if p in self._pattern_config:
    #                 p = self._pattern_config[p]
    #                 seq = self.find_token_sequence(s, p)
    #             else:
    #                 m, g = GU.rematch(p, script)
    #                 if m is None:
    #                     token_list = ["'stop at", len(script)-len(s), "'expected", p, "'through", tuple(token_list)]
    #                     break
    #                 last_post = token_list[len(token_list)-1]
    #                 token_list = token_list[:len(token_list)-1]
    #                 token_list.append(g[p])
    #                 last_post = last_post + m.span()[1]
    #                 token_list.append(last_post)
    #                 s = s[m.span()][1]
    #             token_sequence.append(tuple(token_list))
    #         return tuple(token_sequence)

    def parse(self, script, top):
        pass
        # pattern = self._pattern_config[top]
        # token_seqs = []
        # for patterns in self._pattern_config[top].keys():
        #     for pt in patterns:
        #         for p in pt:
        #
        #         pt = [self._pattern_config[_] for _ in pt]
        #         p = "".join(pt)
        #         m, g = GU.rematch(p, script)
        #         if m is not None:
        #             tok = tuple([(_, g[_]) for _ in pt])
        #             token_seqs.append((tok, script[:m.span()[1]]))


if __name__ == "__main__":
    args = " ".join(sys.argv[1:])
    patterns = {
        "tokens": {
            "$instruction": tuple([("$command", "$args")]),
            "$command": (tuple([r"\s*(P?<$command>[a-zA-Z]+[a-zA-Z0-9_\-]*)"])),
            "$args": (tuple(["$arg"]),
                      ("$args", "$arg")),
            "$arg": (tuple([r"$literal"]),
                     tuple([r"$any"])),
            "$literal": (tuple([r"\s*\"(\"\"|[^\"])*\""])),
            "$any": (tuple([r"\s*[a-zA-Z0-9_!#$%&'=~^|<>\-\(\)\{\}\[\]\W]*"])),
            "$fin": (tuple([r"\s*$"]))
        },
    }
    parser = CommandParser(patterns=patterns)
    print(parser.parse(args, "$instruction"))
