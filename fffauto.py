#!/usr/bin/env python3

import sys
import pathlib
import json
from optparse import OptionParser

OUT_NAME = "fakes"


def generate_fake_function_declaration(name, return_type, args_types) -> str:
    if return_type == 'void':
        return f"DECLARE_FAKE_VOID_FUNC({name}, {','.join(map(str, args_types))});\n"
    else:
        return f"DECLARE_FAKE_VALUE_FUNC({return_type}, {name}, {','.join(map(str, args_types))});\n"


def generate_fake_function_definition(name, return_type, args_types) -> str:
    if return_type == 'void':
        return f"DEFINE_FAKE_VOID_FUNC({name}, {','.join(map(str, args_types))});\n"
    else:
        return f"DEFINE_FAKE_VALUE_FUNC({return_type}, {name}, {','.join(map(str, args_types))});\n"


def generate_fake_functions_list(fakes_list) -> str:
    fake_list_str = "#define FAKE_LIST(FAKE)\t\\\n"
    for i, fake in enumerate(fakes_list):
        if i == (len(fakes_list) - 1):
            fake_list_str += f"\tFAKE({fake})\n"
        else:
            fake_list_str += f"\tFAKE({fake})\t\\\n"
    return fake_list_str


def generate_fake_function_header(json_data, header_name):
    fakes_list = []

    with open(header_name, 'w') as header:
        header.write("#ifndef __AUTO_FAKES_H__\n")
        header.write("#define __AUTO_FAKES_H__\n\n")
        header.write("#include <fff.h>\n")

        header.write("\n/*** AUTO FAKES DECLARATION START ***/\n")
        for fcall in json_data:
            name = fcall["function_name"]
            return_type = fcall["return_value_type"]
            arg_types = fcall["arg_types"]

            header.write(generate_fake_function_declaration(name, return_type, arg_types))
            fakes_list.append(name)

        header.write("/*** AUTO FAKES DECLARATION END ***/\n")

        header.write("\n/*** AUTO FAKES LIST START ***/\n")
        header.write(generate_fake_functions_list(fakes_list))
        header.write("/*** AUTO FAKES LIST END ***/\n")

        header.write("#endif /* __AUTO_FAKES_H__  */\n")


def generate_fake_function_source(json_data, source_name):
    with open(source_name, 'w') as source:
        source.write("#define FFF_GCC_FUNCTION_ATTRIBUTES __attribute__((weak))\n")
        source.write(f"#include \"{OUT_NAME}.h\"\n")
        source.write("DEFINE_FFF_GLOBALS;\n")
        source.write("\n/*** AUTO FAKES DEFINITION START ***/\n")

        for fcall in json_data:
            name = fcall["function_name"]
            return_type = fcall["return_value_type"]
            arg_types = fcall["arg_types"]

            source.write(generate_fake_function_definition(name, return_type, arg_types))

        source.write("/*** AUTO FAKES DEFINITION END ***/\n")


def generate_fakes(json_data, out_dir):
    generate_fake_function_header(json_data, pathlib.Path(out_dir, f"{OUT_NAME}.h"))
    generate_fake_function_source(json_data, pathlib.Path(out_dir, f"{OUT_NAME}.cc"))


def main():
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

    input_file = sys.stdin
    if opts.json is not None:
        input_file = open(opts.json, 'r')

    try:
        json_data = json.load(input_file)
        generate_fakes(json_data, "")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if opts.json is not None:
            input_file.close()


if __name__ == '__main__':
    main()
