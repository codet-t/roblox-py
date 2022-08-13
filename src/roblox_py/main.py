from ..roblox_py.transpiler import transpiler

import ast

def main(arguments):
    folderPath = arguments[1]
    transpilations = transpiler.transpileFolder(folderPath)
    transpilation_results = transpilations["results"];
    transpilation_errors = transpilations["errors"];