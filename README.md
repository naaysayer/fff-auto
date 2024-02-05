Usage

Script for generate [FFF library](https://github.com/meekrosoft/fff) files.
Generate .h header file with 'FAKE_FUNCTION_DECLARATION's and FAKE_LIST. and .cc source file fit 'FAKE_FUNCTION_DEFINITION's.

Designed to be used with [AST-parser](https://github.com/naaysayer/AST-fcall-probe)

Generate from json file with structure:
```json
[
    {
        "function_name": "foo",
        "return_value_type": "int",
        "args": [ "int", "int" ]
    },
    ...
]
```

Usage:
```
Usage: fffauto.py [-j JSON_FILE]

Options:
  -h, --help            show this help message and exit
  -j "FILE.json", --from-json="FILE.json"
                        Json file to load data from
  -o OUT_DIR, --output-dir=OUT_DIR
                        output path
  -n NAME, --name=NAME  Output file names
  -f, --force           Overwrite existing files
  -m, --merge           Merge with existing files after token /* __AUTO_FAKES_MERGE_TOKEN__ */

```

When using -m/--merge, new fakes will be placed after the token /* __AUTO_FAKES_MERGE_TOKEN__ */.
WARRNING: Merge is stupid simple so it would not check existing fakes, it just append new generated strings

In my pipeline, I use a slightly modified version of the FFF library because I need to use the actual header with function declarations for types and other stuff.
The CI pipeline runs as follows:
```
./fcals -p build/ test.c | jq 'map(select(.function_name | test("^mylib")))' | ./fffauto.py -o build
```

That would generate fakes for function called from test.c with prefix 'mylib' into 'build/fakes.cc' and 'build/fakes.h'

