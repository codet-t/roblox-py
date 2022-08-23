from typing import Dict
from ..util import strings as string_util;

from ..transpiler.compile import compile_from_ast as compiler;

import os
import ast

def get_ast_tree(file_path: str) -> Dict[str, str | None]:
    error: str | None = None;
    result: str | None = None;

    # Try to read the file given to us
    try:
        file = open(file_path);
        result = file.read();
    except Exception as e:
        error = file_path + " is not a valid path: " + str(e);

    # Get non-existent file out of the way
    if error != None: return { "error": error };
    # Get non-strings out of the way

    if result is None:
        return { "error": "File is valid" };

    # Try ast.parse(ast.unparse(result))
    parsed: ast.Module | None = None;

    try:
        parsed = ast.parse(result);
    except Exception as e:
        error = "Error parsing file: " + str(e);
    
    if parsed is None:
        return { "error": "Failed to parse file" };

    result = compiler.compile_module(parsed);

    return { "result": result, "error": error };

def transpile_file(file_path: str) -> Dict[str, str | None ]:
    attempt = get_ast_tree(file_path);

    # Get errored file out of the way
    if attempt["error"] != None:
        return attempt;
    
    return { "result": attempt["result"] };

def transpile_folder(folder_origin: str, folder_destination: str, ropy_module_destination: str) -> Dict[str, Dict[str, str | None]]:
    results: Dict[str, str | None] = {};
    errors = {};
    
    full_name: str = "";

    for root, dirs, files in os.walk(folder_origin, topdown=False):
        # Loop through directories and files
        for name in files:
            # Skip non-".py" files
            if not name.endswith(".py"): continue;
            
            # Get full name
            full_name = os.path.join(root, name);

            # Transpile and add the result to result[name]
            transpilation = transpile_file(full_name)

            if "error" in transpilation:
                errors[full_name] = transpilation["error"];

            if "result" in transpilation:
                results[full_name] = transpilation["result"];

    # Empty the destination FOLDER
    for root, dirs, files in os.walk(folder_destination, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name));
        for name in dirs:
            os.rmdir(os.path.join(root, name));

    # Get folder_destination full name
    folder_destination_full_name = os.path.join(os.getcwd(), folder_destination);
    
    # Create and write the results to the destination folder
    for file_name in results:
        name_without_root = full_name.replace(folder_origin + "\\", "");

        new_file_name = os.path.join(folder_destination_full_name, name_without_root)

        # Replace the last .py with .lua
        new_file_name = string_util.replace_reverse(new_file_name, ".py", ".lua", 1);

        os.makedirs(os.path.dirname(new_file_name), exist_ok=True)
        with open(new_file_name, "w") as f:
            f.write(results[file_name] or "")

    ropy_module_destination = ropy_module_destination.replace("/", "\\");
    # Clone ropy_module.lua to ropy_module_destination with the name "ropy.lua", if not exists
    # If exists, modify the contents of ropy_module_destination.["ropy.lua"] to be the contents of ropy_module.lua
    
    # Get the folder of this script
    script_folder = os.path.dirname(os.path.realpath(__file__));

    # Get the root folder of script_folder
    script_folder_root = os.path.dirname(script_folder);

    # Get the ropy_module.lua file from the root folder
    ropy_module_file = os.path.join(script_folder_root, "ropy_module.lua");

    # Get ropy_module_contents
    ropy_module_contents = None;
    with open(ropy_module_file, "r") as f:
        ropy_module_contents = f.read();

    # If the file exists in ropy_module_destination, modify the contents of 
    # this file to be the contents of ropy_module.lua
    ropy_module_name_full = os.path.join(os.getcwd(), ropy_module_destination + "\\ropy.lua");

    if os.path.exists(ropy_module_name_full):
        with open(ropy_module_name_full, "w") as f:
            f.write(ropy_module_contents);

    # If the file does not exist, create a file called "ropy.lua" in ropy_module_destination
    else:
        # Create ropy_module_name_full, with dirs and all
        os.makedirs(os.path.dirname(ropy_module_name_full), exist_ok=True)
        with open(ropy_module_name_full, "w") as f:
            f.write(ropy_module_contents);

    return {"results": results, "errors": errors};