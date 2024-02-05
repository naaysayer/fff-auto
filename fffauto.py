#!/usr/bin/env python3

from pathlib import Path
import sys
import os


def generate_fake_list(function_names: list) -> str:
    fake_list_str = "#define FAKE_LIST(FAKE)\t\\\n"
    for i, fake in enumerate(function_names):
        if i == (len(function_names) - 1):
            fake_list_str += f"\tFAKE({fake})\n"
        else:
            fake_list_str += f"\tFAKE({fake})\t\\\n"
    return fake_list_str


def generate_declaration(name, return_type, args_types) -> str:
    if return_type == 'void':
        return f"DECLARE_FAKE_VOID_FUNC({name}, {','.join(map(str, args_types))});\n"
    else:
        return f"DECLARE_FAKE_VALUE_FUNC({return_type}, {name}, {','.join(map(str, args_types))});\n"


def generate_definition(name, return_type, args_types) -> str:
    if return_type == 'void':
        return f"DEFINE_FAKE_VOID_FUNC({name}, {','.join(map(str, args_types))});\n"
    else:
        return f"DEFINE_FAKE_VALUE_FUNC({return_type}, {name}, {','.join(map(str, args_types))});\n"


def generate_fakes(data: dict, source_filename: str, header_filename: str) -> list:

    source = open(source_filename, 'w')
    header = open(header_filename, 'w')

    header.write("#ifndef __AUTO_FAKES_H__\n")
    header.write("#define __AUTO_FAKES_H__\n\n")
    header.write("#include <fff.h>\n")
    header.write("\n/*** AUTO FAKES DECLARATION START ***/\n")

    source.write("#define FFF_GCC_FUNCTION_ATTRIBUTES __attribute__((weak))\n")
    source.write(f"#include \"{header_filename}.h\"\n")
    source.write("DEFINE_FFF_GLOBALS;\n")
    source.write("\n/*** AUTO FAKES DEFINITION START ***/\n")

    fake_list = []
    for d in data:
        function_name = d["function_name"]
        return_type = d["return_value_type"]
        arg_types = d["arg_types"]

        fake_list.append(function_name)

        source.write(generate_definition(
            function_name, return_type, arg_types))
        header.write(generate_declaration(
            function_name, return_type, arg_types))

    header.write("/*** AUTO FAKES DECLARATION END ***/\n")

    header.write("\n/*** AUTO FAKES LIST START ***/\n")
    header.write(generate_fake_list(fake_list))
    header.write("/*** AUTO FAKES LIST END ***/\n")
    header.write("#endif /* __AUTO_FAKES_H__  */\n")

    source.close()
    header.close()

    return fake_list


def main(opts):
    import json

    # args check
    if not Path(opts.dir).is_dir():
        print(f"Output '{opts.dir}' exptected to be directory",
              file=sys.stderr)
        sys.exit(1)

    source_file = Path(opts.dir, f"{opts.name}.cc")
    header_file = Path(opts.dir, f"{opts.name}.h")

    if (source_file.is_file() or header_file.is_file()) and not opts.force:
        print("Files already exist use -f, --force to overwrite", file=sys.stderr)
        sys.exit(1)

    # read json data from stdin or file
    input_file = sys.stdin
    if opts.json is not None:
        input_file = open(opts.json, 'r')

    json_data = []

    try:
        json_data = json.load(input_file)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if opts.json is not None:
            input_file.close()

    generated_list = generate_fakes(
        json_data, source_file, header_file)

    print(f"Generated {len(generated_list)} fake functions")


if __name__ == '__main__':
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

    parser.add_option(
        "-o",
        "--output-dir",
        dest="dir",
        help="output path",
        metavar="OUT_DIR",
        type=str,
        default=os.getcwd())

    parser.add_option(
        "-n",
        "--name",
        dest="name",
        help="Output file names",
        metavar="NAME",
        type=str,
        default="fakes")

    parser.add_option(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Overwrite existing files",
        default=False)

    parser.disable_interspersed_args()
    (opts, args) = parser.parse_args()

    main(opts)
