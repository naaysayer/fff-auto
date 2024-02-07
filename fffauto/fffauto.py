#!/usr/bin/env python3

from pathlib import Path
import sys
import os

MERGE_TOKEN = "/* __AUTO_FAKES_MERGE_TOKEN__ */\n"


def generate_fake_list(function_names: list) -> str:
    fake_list_str = "#define FAKE_LIST(FAKE)\t\\\n"
    for i, fake in enumerate(function_names):
        if i == (len(function_names) - 1):
            fake_list_str += f"\tFAKE({fake})\n"
        else:
            fake_list_str += f"\tFAKE({fake})\t\\\n"
    return fake_list_str


def generate_declaration(name, return_type, args_types) -> str:
    args_str = ','.join(map(str, args_types))
    if args_str:
        args_str = ', ' + args_str
    if return_type == 'void':
        return f"DECLARE_FAKE_VOID_FUNC({name}{args_str});\n"
    else:
        return f"DECLARE_FAKE_VALUE_FUNC({return_type}, {name}{args_str});\n"


def generate_definition(name, return_type, args_types) -> str:
    args_str = ','.join(map(str, args_types))
    if args_str:
        args_str = ', ' + args_str
    if return_type == 'void':
        return f"DEFINE_FAKE_VOID_FUNC({name}{args_str});\n"
    else:
        return f"DEFINE_FAKE_VALUE_FUNC({return_type}, {name}{args_str});\n"


def merge_source(data: dict, filename: str, tmp_file: str) -> list:
    fakes_list = []
    merged = False

    existing_source = open(filename, 'r')
    new_source = open(tmp_file, 'w')

    for line in existing_source.readlines():
        new_source.write(line)
        if line == MERGE_TOKEN:
            merged = True
            fakes_list = write_fakes(data, new_source, generate_definition)

    existing_source.close()
    new_source.close()

    return merged, fakes_list


def merge_header(data: dict, filename, tmp_file, fake_list) -> bool:
    fakes_list = []
    merged = False

    existing_header = open(filename, 'r')
    new_header = open(tmp_file, 'w')

    for line in existing_header.readlines():
        new_header.write(line)
        if "#define FAKE_LIST(FAKE)" in line:
            for fake in fake_list:
                new_header.write(f"\tFAKE({fake})\t\\\n")
        if MERGE_TOKEN in line:
            merged = True
            fakes_list = write_fakes(data, new_header, generate_declaration)

    existing_header.close()
    new_header.close()

    return merged, fakes_list


def merge_fakes(data: dict, source_filename: str, header_filename: str) -> list:
    fake_list = []
    merged = False

    tmp_src = f"{source_filename}.auto"
    tmp_hdr = f"{header_filename}.auto"

    merged, fake_list = merge_source(data, source_filename, tmp_src)
    if not merged:
        print(
            f"Failed to merge {source_filename}, token not found!", file=sys.stderr)
        os.remove(tmp_src)
        return False, []

    merged, fake_list = merge_header(data, header_filename, tmp_hdr, fake_list)
    if not merged:
        print(
            f"Failed to merge {header_filename}, token not found!", file=sys.stderr)
        os.remove(tmp_hdr)
        os.remove(tmp_src)
        return False, []

    os.rename(tmp_src, source_filename)
    os.rename(tmp_hdr, header_filename)

    return merged, fake_list


def write_fakes(data: dict, file, generator) -> list:
    fake_list = []
    for d in data:
        function_name = d["function_name"]
        return_type = d["return_value_type"]
        arg_types = d["arg_types"]

        fake_list.append(function_name)

        file.write(generator(
            function_name, return_type, arg_types))

    return fake_list


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

    fake_list = write_fakes(data, header, generate_declaration)
    write_fakes(data, source, generate_definition)

    header.write(MERGE_TOKEN)
    source.write(MERGE_TOKEN)

    header.write("/*** AUTO FAKES DECLARATION END ***/\n")

    header.write("\n/*** AUTO FAKES LIST START ***/\n")
    header.write(generate_fake_list(fake_list))
    header.write("/*** AUTO FAKES LIST END ***/\n")
    header.write("#endif /* __AUTO_FAKES_H__  */\n")

    source.close()
    header.close()

    return fake_list


def main():
    from optparse import OptionParser
    import json

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

    parser.add_option(
        "-m",
        "--merge",
        dest="merge",
        action="store_true",
        help=f"Merge with existing files after token {MERGE_TOKEN}",
        default=False)

    parser.disable_interspersed_args()
    (opts, args) = parser.parse_args()

    # args check
    if not Path(opts.dir).is_dir():
        print(f"Output '{opts.dir}' exptected to be directory",
              file=sys.stderr)
        sys.exit(1)

    source_file = Path(opts.dir, f"{opts.name}.cc")
    header_file = Path(opts.dir, f"{opts.name}.h")

    if source_file.is_file() or header_file.is_file():
        if not (opts.force or opts.merge):
            print("Files already exist use -f, --force to overwrite or -m, --merge to try to merge it",
                  file=sys.stderr)
            sys.exit(1)
    else:
        if opts.merge:
            print("Merge option set, but files not exist. Check your path!")
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

    if opts.merge:
        merged, generated_list = merge_fakes(json_data, source_file, header_file)
        if not merged:
            sys.exit(1)
    else:
        generated_list = generate_fakes(
            json_data, source_file, header_file)

    print(f"Generated {len(generated_list)} fake functions")


if __name__ == '__main__':
    main()