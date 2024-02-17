Generate [FFF library](https://github.com/meekrosoft/fff) files, with fakes function parsed from source files AST.

Usage:
```
usage: autofff.py [-h] [--dry-run] [--exclude [EXCLUDE ...]] [-p PATH] [-v] [-f] [--store-cache] [-m] [--single-file] [-r REGEX] [-o OUT] [FILE] [CFLAGS ...]

Generate FFF library fakes from source files. Fakes generated from expression in AST of a source file using regex

positional arguments:
  FILE                  source file to generate fakes from, if not set fakes would be generated for all files from compilation db
  CFLAGS                compiler flags, write -- before specify flags

options:
  -h, --help            show this help message and exit
  --dry-run             Do not generate/write fakes into files
  --exclude [EXCLUDE ...]
                        Exclude path from processing, used while processing files from compilation db
  -p PATH, --build-path PATH
                        Path to directory that contains clang compilation_commands.json
  -v, --verbose         print debug information
  -f, --force           overwrite existing files
  -m, --merge           Merge with existing files. Generated fake would be added after string contains "/* __AUTO_FFF_MERGE_TOKEN__ */"
  --single-file         Generate only source file
  -r REGEX, --regex REGEX
                        regex to match expressions
  -o OUT, --output OUT  Output filename without extension .cc and .h files would generated with this name. Default autofakes.h/cc
```

Note:

You need to install libclang:
```
	pip install libclang
```

if `regex` not specified all function declaration and expression would be taken, as fakes.

Example:

Getting all function call from 'my_lib'( assuming all function have prefix 'my_lib'), from all sources files in compile_commands.json except build and test directory.
```
python3 fffauto.py --exclude ./build ./test -r "^my_lib" --merge -p build
```