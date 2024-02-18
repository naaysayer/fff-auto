#!/usr/bin/env python3

import logging
import sys
import json
import os

from fffauto import fff

from clang.cindex import TranslationUnitLoadError
from pathlib import Path

MERGE_TOKEN_STRING = "/* __AUTO_FFF_MERGE_TOKEN__ */"
DEFAULT_FILENAME = "autofakes"
CACHE_FILENAME = ".autofakes_cache"


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.ERROR)


def _cache(out: str, data: list[fff.Fake]) -> list[fff.Fake]:
    import pickle

    path = f"{os.path.dirname(out)}/{CACHE_FILENAME}"

    cached = []

    if os.path.exists(path):
        with open(path, 'rb') as cache:
            cached = pickle.load(cache)

    diff = [item for item in data if item not in cached]

    with open(path, 'wb') as cache:
        pickle.dump(data, cache)

    return diff


def _path_excluded(path: str, excluded_paths: list[str]) -> bool:
    for excluded in excluded_paths:
        if excluded in path:
            return True
    return False


def _read_compile_commands(filepath: Path,
                           specific_file: str = None,
                           exclude_paths: list[str] = None) -> list[dict]:

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
            _path = os.path.realpath(os.path.dirname(cmd['file']))
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
        prog='fffauto',
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
    parser.add_argument('--no-cache',
                        help='Do not save cached values and do not use cache if exists',
                        action='store_true')
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

    if not args.FILE and not args.path:
        logging.critical('Not enough arguments')
        sys.exit(1)

    if args.verbose:
        logging.root.setLevel(logging.DEBUG)

    source_filename = f'{args.out}.cc'
    header_filename = f'{args.out}.h' if not args.single_file else None

    logging.info(f"Output files {source_filename},{header_filename}")

    if args.exclude:
        args.exclude = [os.path.realpath(path) for path in args.exclude]

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

        file_cmd = _read_compile_commands(compiledb_file,
                                          args.FILE, args.exclude)
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

    if not args.no_cache:
        fakes_list = _cache(args.out, fakes_list)
        logging.info(f"Found {len(fakes_list)} not cached fakes")
    else:
        logging.info(f"Found {len(fakes_list)} unique fakes")

    if not fakes_list:
        logging.info('Nothing to do here')
        sys.exit(0)

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
