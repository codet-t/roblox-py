import os
import json
import time

import src.roblox_py.transpiler.transpiler as transpiler

settings = {};

def get_settings():
    # Check if the current folder has a "ropy.json" file in it
    if not os.path.isfile("ropy.json"):
        print("Error: ropy.json not found in " + os.getcwd());
        exit();
    
    # Read the file
    file = open("ropy.json");
    settings = file.read();
    settings = json.loads(settings);

    if "outDirectory" not in settings:
        print("Error: outDirectory not found in ropy.json");
        exit();

    if "inDirectory" not in settings:
        print("Error: inDirectory not found in ropy.json");
        exit();

    # Reject any foreign settings
    for setting in settings:
        if setting not in ["outDirectory", "inDirectory"]:
            print("Error: " + setting + " is not a valid setting");
            exit();

    # Check if settings["outDirectory"] and settings["inDirectory"] is a valid directory
    if not os.path.isdir(settings["inDirectory"]):
        print("Error: " + settings["inDirectory"] + " is not a valid directory");
        exit();

    if not os.path.isdir(settings["outDirectory"]):
        print("Error: " + settings["outDirectory"] + " is not a valid directory");
        exit();
    
    return settings;

def transpile(folderOrigin: str, folderDestination: str):
    start_time = int(round(time.time() * 1000))

    transpilations = transpiler.transpile_folder(folderOrigin, folderDestination)

    transpilation_results = transpilations["results"];
    transpilation_errors = transpilations["errors"];

    if len(transpilation_errors) > 0:
        print("Error:")
        for error in transpilation_errors:
            print(error)
        return
    
    empty = 0;

    for file in transpilation_results:
        if transpilation_results[file] == "" or transpilation_results[file] == None:
            empty += 1;
            continue;

    print("Successfully transpiled " + str(len(transpilation_results)) + " files (" + str(empty) + " of which were empty) in " + str(int(round(time.time() * 1000)) - start_time) + " ms");

def main():
    settings = get_settings();
    transpile(settings["inDirectory"], settings["outDirectory"]);