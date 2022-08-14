from unittest import result
from ..util import transpilation as transpilation_util;
from ..util import strings as string_util;

import os
import re
import ast

def transpileFile(filePath: str) -> dict[str, str]:
    result: any = None;
    error: str | None = None;

    # Try to read the file given to us
    try:
        file = open(filePath);
        result = file.read();
    except Exception as e:
        error = filePath + " is not a valid path: " + str(e);
    
    # Get non-existent file out of the way
    if error != None: return { "error": error };

    # Get non-strings out of the way
    if not isinstance(result, str): return { "error": "File is valid" };

    # Try ast.parse(ast.unparse(result))
    try:
        result = ast.parse(result);
        result = ast.unparse(result);
    except Exception as e:
        error = "Error parsing file: " + str(e);

    # Get errored file out of the way
    if error != None: return { "error": error };

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

    result = "--Transpiled with roblox-py" + "\n".join(lines)
    
    return { "result": result };

def transpileFolder(folderOrigin: str, folderDestination: str) -> dict[str, str]:
    results = {};
    errors = {};

    for root, dirs, files in os.walk(folderOrigin, topdown=False):
        # Loop through directories and files
        for name in files:
            # Skip non-".py" files
            if not name.endswith(".py"): continue;
            
            # Get full name
            fullName = os.path.join(root, name);

            # Transpile and add the result to result[name]
            transpilation = transpileFile(fullName)

            if "error" in transpilation:
                errors[fullName] = transpilation["error"];

            if "result" in transpilation:
                results[fullName] = transpilation["result"];

    # Empty the destination FOLDER
    for root, dirs, files in os.walk(folderDestination, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name));
        for name in dirs:
            os.rmdir(os.path.join(root, name));

    # Get folderDestination full name
    folderDestinationFullName = os.path.join(os.getcwd(), folderDestination);
    
    # Create and write the results to the destination folder
    for fullName in results:
        nameWithoutRoot = fullName.replace(folderOrigin + "\\", "");

        newFileName = os.path.join(folderDestinationFullName, nameWithoutRoot)

        # Replace the last .py with .lua
        newFileName = string_util.replace_reverse(newFileName, ".py", ".lua", 1);

        os.makedirs(os.path.dirname(newFileName), exist_ok=True)
        with open(newFileName, "w") as f:
            f.write(results[fullName])

    return {"results": results, "errors": errors};