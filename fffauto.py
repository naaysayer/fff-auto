#!/usr/bin/env python3

import sys
import json
import os


OUT_NAME = "fakes"


def fff_generate(json):
    header = open(f"{OUT_NAME}.h", 'w')
    source = open(f"{OUT_NAME}.cc", 'w')

    header.write("#ifndef __AUTO_FAKES_H__\n")
    header.write("#define __AUTO_FAKES_H__\n")

    fakes_list = []

    for fdata in json:
        name = fdata["function_name"]
        return_type = fdata["return_value_type"]
        argc = fdata["argc"]
        args_types = fdata["arg_types"]

        fakes_list.append(name)

    # print FAKE_LIST
    header.write("#define FAKE_LIST(FAKE) \t\\\n")
    for i in range(len(fakes_list)):
        if i == (len(fakes_list) - 1):
            header.write(f"\tFAKE({fakes_list[i]})\t\n")
        else:
            header.write(f"\tFAKE({fakes_list[i]})\t\\\n")

    # close include guards
    header.write("#endif /* __AUTO_FAKES_H__*/\n")


def main():
    from optparse import OptionParser

    parser = OptionParser("usage: %prog [-j JSON_FILE]")
    parser.add_option(
        "-j",
        "--from-json",
        dest="json",
        help="Json file to load data from",
        metavar="\"FILE.json\"",
        type=str,
        default=None)

    parser.disable_interspersed_args()
    (opts, args) = parser.parse_args()

    input = sys.stdin
    if opts.json is not None:
        input = open(opts.json, 'r')

    json_data = json.load(input)

    fff_generate(json_data)



if __name__ == '__main__':
    main()
