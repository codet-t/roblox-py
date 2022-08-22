from ..util import transpilation as transpilation_util;
from ..util import strings as string_util;

from ..transpiler.compile import compile_from_ast as compiler;

import os
import ast

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

    result = compiler.compile_module(parsed);

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

    module_folder = "";
    
    # Create and write the results to the destination folder
    for full_name in results:
        name_without_root = full_name.replace(folder_origin + "\\", "");

        new_file_name = os.path.join(folder_destination_full_name, name_without_root)

        # Replace the last .py with .lua
        new_file_name = string_util.replace_reverse(new_file_name, ".py", ".lua", 1);

        os.makedirs(os.path.dirname(new_file_name), exist_ok=True)
        with open(new_file_name, "w") as f:
            f.write(results[full_name] or "")
    
        # Check if file_path ends in either .client.py or .server.py
    
        if (new_file_name.endswith(".lua") and 
        not new_file_name.endswith(".client.lua") and
        not new_file_name.endswith(".server.lua")):
            module_folder = os.path.dirname(new_file_name);
    
    # Get folder of this script
    script = os.path.dirname(os.path.realpath(__file__));
    
    # Get folder of script
    script_folder = os.path.dirname(script);

    # Get ropy_module.lua in script_folder
    ropy_module = os.path.join(script_folder, "ropy_module.lua");

    # Clone ropy_module.lua to module_folder
    os.system("copy " + ropy_module + " " + module_folder);

    # Rename ropy_module.lua to ropy.lua
    os.rename(os.path.join(module_folder, "ropy_module.lua"), os.path.join(module_folder, "ropy.lua"));

    return {"results": results, "errors": errors};