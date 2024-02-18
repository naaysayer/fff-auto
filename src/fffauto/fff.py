#!/usr/bin/env python3
from clang import cindex
import re

from fffauto import ast

# for some node.kinds arguments are empty, but node.type contains info about arguments like that int(int arg1, char)
_ftype_pattern = re.compile(
    r'(?P<return_type>\w+(\s\*)?)\s?\(\s*(?P<arg_types>.*?)\s*\)(?:\s*\(\*\))?')

MERGE_TOKEN_STRING = "/* __AUTO_FFF_MERGE_TOKEN__ */\n"
FAKE_LIST_STR = "#define FFF_FAKE_LIST(FAKE)\\\n"


class Fake:
    """
    Represents a EXPRESSION or FUNCTION_DECLARATION parsed from ast with cland.cindex

    Attributes:
        spelling (str): The name of the function.
        arg_types (list[str] or None): The list of argument types, or None if there are no arguments.
        return_type (str or None): The return type of the function, or None for void functions.
    """
    spelling: str
    arg_types: list[str]
    return_type: str

    def __init__(self, ast_node: cindex.Cursor):
        self.spelling = ast_node.spelling
        self.return_type = ast_node.type.spelling
        self.arg_types = [
            arg.type.spelling for arg in ast_node.get_arguments()]

        match = _ftype_pattern.search(self.return_type)

        if match:
            self.return_type = match.group('return_type')
            self.arg_types = [
                arg.strip() for arg in match.group('arg_types').split(',')
            ] if match.group('arg_types') else None

    def _generate_fake(self, prefix: str = "") -> str:
        generated = prefix
        if self.return_type is None or self.return_type == 'void':
            generated += 'FAKE_VOID_FUNC('
        else:
            generated += 'FAKE_VALUE_FUNC('
            generated += self.return_type
            generated += ', '

        generated += self.spelling

        if self.arg_types:
            generated += f", {','.join(map(str, self.arg_types))}"

        generated += ');\n'

        return generated

    def get_declaration(self) -> str:
        """
        Get the FFF fake function declaration macro string
        example: DECLARE_FAKE_VALUE_FUNC(int, foo, char)
        """
        return self._generate_fake('DECLARE_')

    def get_definition(self) -> str:
        """
        Get FFF fake function defenition macro string,
        used when there is a header file with fake function declaration macro
        example: DEFINE_FAKE_VALUE_FUNC(int, foo, char)
        """
        return self._generate_fake('DEFINE_')

    def get_define(self) -> str:
        """
        Get FFF fake function defenition macro string,
        used when there is no header file with fake function declaration macro
        example: FAKE_VALUE_FUNC(int, foo, char)
        """
        return self._generate_fake()

    def get_fake_list_entry(self, last: bool = False) -> str:
        """
        Helper function that return string used in macro defenition,
        when last there is no '\' on the end of a string
        """
        if last:
            return f" FAKE({self.spelling})\n"
        else:
            return f" FAKE({self.spelling})\\\n"


def generate_fake_list(fakes: list[Fake]) -> str:
    fake_list_str = FAKE_LIST_STR

    for i, fake in enumerate(fakes):
        last: bool = (i == len(fakes) - 1)
        fake_list_str += fake.get_fake_list_entry(last)

    return fake_list_str


def generate_header(fakes: list[Fake]) -> str:
    header_str = """
#ifndef __AUTO_FAKES_H__
#define __AUTO_FAKES_H__

#include <fff.h>

"""

    header_str += '\n'.join([fake.get_declaration() for fake in fakes])

    header_str += '\n\n'
    header_str += generate_fake_list(fakes)

    header_str += '\n\n'

    header_str += MERGE_TOKEN_STRING
    header_str += '\n\n'

    header_str += '#endif  /*  __AUTO_FAKES_H__  */"'

    return header_str


def generate_source(fakes: list[Fake], header_name: str | None) -> str:
    source_str = """#define FFF_GCC_FUNCTION_ATTRIBUTES __attribute__((weak))

DEFINE_FFF_GLOBALS;

"""
    if header_name:
        source_str += f"#include \"{header_name}\""
        source_str += '\n\n'
        source_str += '\n'.join([fake.get_definition() for fake in fakes])
    else:
        source_str += "\n#include <fff.h>\n"
        source_str += '\n'.join([fake.get_define() for fake in fakes])

    source_str += MERGE_TOKEN_STRING
    source_str += '\n\n'

    return source_str


def get_fakes(compile_commands: list[dict],
              regex: str | None = None,
              show_progress: bool = False) -> list[Fake]:

    import sys

    match_re = re.compile(regex) if regex is not None else None

    def matcher(node: cindex.Cursor) -> bool:
        if (not node.kind.is_expression() and
                node.kind != cindex.CursorKind.FUNCTION_DECL):
            return False

        if not node.spelling:
            return False

        if regex is not None:
            match = match_re.match(node.spelling)
            if not match:
                return False

        return True

    fakes = {}
    for command in compile_commands:
        index = ast.Ast(command['file'], command['command'])

        count = 0
        if show_progress:
            sys.stdout.write(f'{index.get_spelling()}...')

        for node in index.get_matched(matcher):
            if ((node.spelling not in fakes) or
                (node.kind == cindex.CursorKind.CALL_EXPR or
                 node.kind == cindex.CursorKind.FUNCTION_DECL)):
                fakes[node.spelling] = node
                count += 1

        if show_progress:
            sys.stdout.write(f'{count}\n')
        count = 0

    return [Fake(node) for name, node in fakes.items()]


def _merge_into(filename: str,
                merge_data: dict[str:list[str]]) -> bool:

    with open(filename, 'r') as file:
        content = file.read()

    for token, strings in merge_data.items():
        token_index = content.find(token)

        if token_index != -1:
            new_content = content[:token_index + len(token)] + ''.join(strings) + content[token_index + len(token):]
            print(f"found token {token} in{filename} at {token_index}")
        else:
            raise Exception(
                    f'Failed to merge into {filename} token {token} not found')
        content = new_content

    with open(filename, 'w') as file:
        file.write(new_content)


def write_source_file(filename: str,
                      fake_list: list[Fake],
                      include_header: str | None = None,
                      allow_merge=False,
                      allow_overwrite=False):
    import os

    if os.path.exists(filename):
        if not allow_merge and not allow_overwrite:
            raise Exception(
                    f'{filename} file exist, but merge not allowed')

        if include_header:
            _merge_into(filename,
                        {MERGE_TOKEN_STRING:
                         [fake.get_definition() for fake in fake_list]})
        else:
            _merge_into(filename,
                        {MERGE_TOKEN_STRING:
                         [fake.get_define() for fake in fake_list]})

    else:
        with open(filename, 'w') as file:
            file.write(generate_source(fake_list, include_header))


def write_header_file(filename: str,
                      fake_list: list[Fake],
                      allow_merge=False,
                      allow_overwrite=False):
    import os

    if os.path.exists(filename):
        if not allow_merge and not allow_overwrite:
            raise Exception(
                    f'{filename} file exist, but merge/overwrite not allowed')

        _merge_into(filename,
                    {
                        MERGE_TOKEN_STRING: [fake.get_declaration() for fake in fake_list],
                        FAKE_LIST_STR: [fake.get_fake_list_entry() for fake in fake_list]
                     })
    else:
        with open(filename, 'w') as file:
            file.write(generate_header(fake_list))
