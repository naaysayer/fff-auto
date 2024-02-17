#!/usr/bin/env python3

import logging
import sys
import fffauto.fff as fff
import json
import os

from clang.cindex import TranslationUnitLoadError
from pathlib import Path

MERGE_TOKEN_STRING = "/* __AUTO_FFF_MERGE_TOKEN__ */"
DEFAULT_FILENAME = "autofakes"


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.ERROR)


def _path_excluded(path: Path, excluded_paths: list[Path]) -> bool:
    if path in excluded_paths:
        return True

    for exclude_path in excluded_paths:
        if exclude_path in path.parents:
            return True

    return False


def _read_compile_commands(filepath: Path,
                           specific_file: str = None,
                           exclude_paths: list[Path] = None) -> list[dict]:

    commands = dict()

    with open(filepath, 'r') as compile_db:
        try:
            commands = json.load(compile_db)
        except FileNotFoundError:
            logging.error(f"Can't open {filepath}: File not found!")
            return []
        except json.decoder.JSONDecodeError:
            logging.error(
                f"Can't read compile_db {filepath} : Bad json format!")
            return []

    if not specific_file:
        _compile_db = []
        for cmd in commands:
            _path = Path(os.path.dirname(cmd['file']))
            if not exclude_paths or not _path_excluded(_path, exclude_paths):
                _compile_db.append({
                    'file': None,
                    'command': cmd['command'].split(' ')
                })
        return _compile_db

    for command in commands:
        if specific_file in command['file']:
            return [{
                    'file': None,
                    'command': command['command'].split(' ')
                    }]

    logging.error(f"File {specific_file} not found in compile_db {filepath}")

    return []


def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog='autofff.py',
        description="""
            Generate FFF library fakes from source files.
            Fakes generated from expression in AST of a source file using regex
            """,
        epilog='FFF library docs availabe here https://github.com/meekrosoft/fff')

    parser.add_argument('FILE',
                        help='''source file to generate fakes from,
                        if not set fakes would be generated for all files from compilation db''',
                        nargs='?')
    parser.add_argument('CFLAGS',
                        help='compiler flags, write -- before specify flags',
                        nargs='*')
    parser.add_argument('--dry-run', dest='dry_run',
                        help="Do not generate/write fakes into files",
                        action='store_true')
    parser.add_argument('--exclude', dest='exclude',
                        help='Exclude path from processing, used while processing files from compilation db',
                        nargs='*')
    parser.add_argument('-p', '--build-path', dest='path',
                        help='Path to directory that contains clang compilation_commands.json')
    parser.add_argument('-v', '--verbose',
                        help='print debug information',
                        action='store_true')
    parser.add_argument('-f', '--force',
                        help='overwrite existing files',
                        action='store_true')
    parser.add_argument('-m', '--merge',
                        help=f"""Merge with existing files.
                        Generated fake would be added after
                        string contains \"{MERGE_TOKEN_STRING}\"""",
                        action='store_true')
    parser.add_argument('--single-file', dest='single_file',
                        help='Generate only source file',
                        action='store_true')
    parser.add_argument('-r', '--regex', type=str, dest='regex',
                        help='regex to match expressions')
    parser.add_argument('-o', '--output',
                        help=f"""Output filename without extension
                        .cc and .h files would generated with this name.\n
                        Default {DEFAULT_FILENAME}.h/cc""",
                        type=str, dest='out',
                        default=DEFAULT_FILENAME)

    args = parser.parse_args()

    if args.verbose:
        logging.root.setLevel(logging.DEBUG)

    source_filename = f'{args.out}.cc'
    header_filename = f'{args.out}.h' if not args.single_file else None

    logging.info(f"Output files {source_filename},{header_filename}")

    if args.exclude:
        args.exclude = [Path(os.path.realpath(path)) for path in args.exclude]

    file_cmd = dict()

    if args.path:
        compiledb_file = Path(args.path, 'compile_commands.json')
        if not compiledb_file.is_file():
            logging.error(f"""Failed to load compilation db:
                          compile_commands.json not found in {args.path}""")
            sys.exit(1)

        if args.CFLAGS:
            logging.warning('''
                Fakes would be generated only for specified file,
                compiler flags would be taken from file.
                Rest of files would be ignored''')

        file_cmd = _read_compile_commands(compiledb_file, args.FILE, args.exclude)
    else:
        file_cmd = [{
                'file': args.FILE,
                'command': args.CFLAGS,
                'directory': os.path.dirname(args.FILE)
                }]

    if not file_cmd:
        sys.exit(1)

    try:
        fakes_list = fff.get_fakes(file_cmd, args.regex, args.verbose)
    except TranslationUnitLoadError as e:
        logging.error(e)
        sys.exit(1)

    if not fakes_list:
        logging.info('Nothing to do here')
        sys.exit(0)

    logging.info(f"Found unique {len(fakes_list)}")

    if args.dry_run:
        sys.exit(0)

    try:
        fff.write_source_file(source_filename,
                              fakes_list,
                              header_filename,
                              allow_merge=args.merge,
                              allow_overwrite=args.force)

        if header_filename:
            fff.write_header_file(header_filename,
                                  fakes_list,
                                  allow_merge=args.merge,
                                  allow_overwrite=args.force)
    except Exception as e:
        logging.error(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
