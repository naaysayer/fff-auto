#!/usr/bin/env python3

from dataclasses import dataclass


@dataclass
class Fake:
    spelling: str
    arg_types: list[str]
    return_type: str

    def argTypesStr(self):
        return ','.join(map(str, self.arg_types))


def generate_fake(fake: Fake, prefix: str = "") -> str:
    generated = prefix
    if fake.return_type is None:
        generated += 'FAKE_VOID_FUNC('
    else:
        generated += 'FAKE_VALUE_FUNC('

    generated += fake.spelling

    if fake.arg_types:
        generated += f", {fake.argTypesStr()}"

    generated += ');'

    return generated


def generate_fake_declaration(fake: Fake) -> str:
    return generate_fake(fake, 'DECLARE_')


def generate_fake_definition(fake: Fake) -> str:
    return generate_fake(fake, 'DEFINE_')


def generate_fake_list(fakes: list[Fake]) -> str:
    fake_list_str = "#define FFF_FAKE_LIST(FAKE)\t\\\n"

    for i, fake in enumerate(fakes):
        if i < len(fakes) - 1:
            fake_list_str += f"\tFAKE({fake.spelling})\t\\\n"
        else:
            fake_list_str += f"\tFAKE({fake.spelling})\n"

    return fake_list_str


def generate_header(fakes: list[Fake]) -> str:
    header_str = """
        #ifndef __AUTO_FAKES_H__
        #define __AUTO_FAKES_H__

        #include <fff.h>

    """

    header_str += '\n'.join([generate_fake_declaration(fake) for fake in fakes])

    header_str += generate_fake_list(fakes)

    header_str += "#endif  /*  __AUTO_FAKES_H__  */"

    return header_str


def generate_source(fakes: list[Fake], header_name: str) -> str:
    source_str = """
    #define FFF_GCC_FUNCTION_ATTRIBUTES __attribute__((weak))

    DEFINE_FFF_GLOBALS;

    """
    if header_name:
        source_str += f"\n#include \"{header_name}\""
        source_str += '\n'.join([generate_fake_definition(fake) for fake in fakes])
    else:
        source_str += "\n#include <fff.h>"
        source_str += generate_fake_list(fakes)
        source_str += '\n'.join([generate_fake(fake) for fake in fakes])

    return source_str
