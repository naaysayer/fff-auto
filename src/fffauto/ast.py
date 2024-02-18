#!/usr/bin/env python3

from typing import Callable
from clang import cindex


class Ast:
    """
    Represents an Abstract Syntax Tree (AST) for a C or C++ source file.

    Args:
        filename (str): The path to the C or C++ source file.
        compiler_flags (list[str]): List of compiler flags to be used during parsing.

    Attributes:
        __translation_unit: The parsed translation unit, obtained from the clang library.

    Methods:
        get_spelling(): Get the spelling of the translation unit.
        get_matched(matcher: Callable[[cindex.Cursor], bool] | None): Yield AST nodes that match the given criteria.
        __traverse(node: cindex.Cursor): Recursively traverse the AST starting from the given node.

    Example:
        >>> ast = Ast("example.c", ["-Wall", "-std=c11"])
        >>> spelling = ast.get_spelling()
        >>> print(f"Spelling of the translation unit: {spelling}")
        >>> def matcher(node):
        ...     # Your matching criteria implementation
        ...     return True
        >>> matched_nodes = list(ast.get_matched(matcher))
        >>> print(f"Number of matched nodes: {len(matched_nodes)}")
    """

    def __init__(self, filename: str, compiler_flags: list[str]):
        """
        Initialize the Ast object by parsing the given source file.

        Args:
            filename (str): The path to the C or C++ source file.
            compiler_flags (list[str]): List of compiler flags to be used during parsing.
        """
        index = cindex.Index.create()
        self.__translation_unit = index.parse(filename, compiler_flags)

    def get_spelling(self):
        """
        Get the spelling of the translation unit.

        Returns:
            str: The spelling of the translation unit.
        """
        return self.__translation_unit.spelling

    def get_matched(self, matcher: Callable[[cindex.Cursor], bool] | None):
        """
        Yield AST nodes that match the given criteria.

        Args:
            matcher (Callable[[cindex.Cursor], bool] | None): A callable function that takes a cindex.Cursor and
                returns a boolean indicating whether the node matches the criteria. If None, all nodes are yielded.

        Yields:
            cindex.Cursor: AST nodes that match the given criteria.
        """
        for node in self.__traverse(self.__translation_unit.cursor):
            if not matcher or matcher(node):
                yield node

    def __traverse(self, node: cindex.Cursor):
        """
        Recursively traverse the AST starting from the given node.

        Args:
            node (cindex.Cursor): The starting node for the traversal.

        Yields:
            cindex.Cursor: AST nodes encountered during the traversal.
        """
        yield node

        for child in node.get_children():
            yield from self.__traverse(child)
