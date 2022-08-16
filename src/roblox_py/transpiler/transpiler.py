from tarfile import PAX_FORMAT
from ..util import transpilation as transpilation_util;
from ..util import strings as string_util;

import os
import ast
import re

def get_ast_tree(file_path: str) -> dict[str, str]:
    result: any = None;
    error: str | None = None;

    # Try to read the file given to us
    try:
        file = open(file_path);
        result = file.read();
    except Exception as e:
        error = file_path + " is not a valid path: " + str(e);

    # Get non-existent file out of the way
    if error != None: return { "error": error };
    # Get non-strings out of the way

    if not isinstance(result, str): return { "error": "File is valid" };

    # Try ast.parse(ast.unparse(result))
    try:
        parsed: ast.AST = ast.parse(result);
    except Exception as e:
        error = "Error parsing file: " + str(e);

    result = transpilation_util.transpile_module(parsed);

    return { "result": result, "error": error };

def transpile_file(file_path: str) -> dict[str, str]:
    attempt = get_ast_tree(file_path);

    # Get errored file out of the way
    if attempt["error"] != None: return attempt;
    
    return { "result": attempt["result"] };

def transpile_folder(folder_origin: str, folder_destination: str) -> dict[str, str]:
    results = {};
    errors = {};

    for root, dirs, files in os.walk(folder_origin, topdown=False):
        # Loop through directories and files
        for name in files:
            # Skip non-".py" files
            if not name.endswith(".py"): continue;
            
            # Get full name
            fullName = os.path.join(root, name);

            # Transpile and add the result to result[name]
            transpilation = transpile_file(fullName)

            if "error" in transpilation:
                errors[fullName] = transpilation["error"];

            if "result" in transpilation:
                results[fullName] = transpilation["result"];

    # Empty the destination FOLDER
    for root, dirs, files in os.walk(folder_destination, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name));
        for name in dirs:
            os.rmdir(os.path.join(root, name));

    # Get folder_destination full name
    folder_destination_full_name = os.path.join(os.getcwd(), folder_destination);
    
    # Create and write the results to the destination folder
    for fullName in results:
        name_without_root = fullName.replace(folder_origin + "\\", "");

        newFileName = os.path.join(folder_destination_full_name, name_without_root)

        # Replace the last .py with .lua
        newFileName = string_util.replace_reverse(newFileName, ".py", ".lua", 1);

        os.makedirs(os.path.dirname(newFileName), exist_ok=True)
        with open(newFileName, "w") as f:
            f.write(results[fullName])

    return {"results": results, "errors": errors};