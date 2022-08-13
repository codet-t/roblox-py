from ..util import transpilation as transpilation_util;

import os
import re
import ast

def transpileFile(filePath: str) -> dict[str, str]:
    result = None;
    error = None;

    # Try to read the file given to us
    try:
        file = open(filePath);
        result = file.read();
    except Exception as e:
        error = filePath + " is not a valid path: " + str(e);
    
    # Get non-existent file out of the way
    if error != None: return { "result": None, "error": error };

    # Get non-strings out of the way
    if not isinstance(result, str): return { "result": None, "error": "File is not a string" };

    # Try ast.parse(ast.unparse(result))
    try:
        result = ast.parse(result);
        result = ast.unparse(result);
    except Exception as e:
        error = "Error parsing file: " + str(e);

    # Get errored file out of the way
    if error != None: return { "result": None, "error": error };

    # Turn every ":" into a ":" plus whiteline
    result = re.sub(r":", r":\n", result);

    # Turn every ";" into a ";" plus whiteline
    result = re.sub(r";", r";\n", result);

    # Remove every double whiteline twice
    result = re.sub(r"\n\n", r"\n", result);
    result = re.sub(r"\n\n", r"\n", result);

    # Split by whiteline
    lines = result.split("\n");

    # Remove every line that is not a string, has a length of 0, consists entirely of spaces or newlines
    lines[:] = [x for x in lines if x.strip()]

    # Deal with identation and replacing def with function, elif with else if
    transpilation_util.deal_with_indentation(lines);
    
    return { "result": "\n".join(lines), "error": error };

def transpileFolder(folderPath: str) -> dict[str, str]:
    results = {};
    errors = {};

    for root, dirs, files in os.walk(folderPath, topdown=False):
        # Loop through directories and files
        for name in files:
            # Skip non-".py" files
            if not name.endswith(".py"): continue;
            
            # Transpile and add the result to result[name]
            transpilation = transpileFile(os.path.join(root, name))

            if "error" in transpilation:
                errors[len(errors)] = transpilation["error"];

            if "result" in transpilation:
                print(transpilation["result"])
                results[len(results)] = transpilation["result"];


    return {"results": results, "errors": errors};