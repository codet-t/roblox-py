from socket import has_dualstack_ipv6
from typing import List

import ast as py_ast;

from ..analysis.build_lua_ast import map_module
from ..lua_ast import lua_ast_nodes as lua_ast
from ..lua_ast.lua_scope import Scope

top_scope = Scope("0", "top", [], [], None)

options = {
    "toggle_ast": True,
    "toggle_scope_ids": True,
}

def initialise_string(node: any, scope: Scope) -> str:
    result = "";

    if options["toggle_ast"]:
        result = result + "--[[" + node.__class__.__name__ + "]]"

    if options["toggle_scope_ids"]:
        result = result + "--[[ ScopeId: " + scope.scope_id + "]]";
    
    return result;

def compile_if(if_node: lua_ast.IfNode, scope: Scope):
    result = initialise_string(if_node, scope);

    scope.add_child("if", if_node);

    result = result + "if " + compile_expression(if_node.condition, scope) + " then";
    result = result + compile_lines(if_node.body, scope);
    result = result + "end";

    return result;

def compile_function(function_node: lua_ast.FunctionNode, scope: Scope) -> str:
    result = initialise_string(function_node, scope);

    scope.add_child("function", function_node);

    result = result + "function " + function_node.name + "(";

    for arg in function_node.args:
        result = result + arg.identifier
        if arg != function_node.args[-1]:
            result = result + ", ";

    result = result + ")";
    result = result + compile_lines(function_node.body, scope);
    result = result + "end";

def compile_name(name_node: lua_ast.NameNode, scope: Scope) -> str:
    result = initialise_string(name_node, scope);

    result = result + name_node.name;

    return result;

def compile_compoperator(operator_node: lua_ast.CompareOperatorNode, left: lua_ast.Node, right: lua_ast.Node, scope: Scope) -> str:
    result = initialise_string(operator_node, scope);

    if operator_node.parenthesis:
        result = result + operator_node.operator
        result = result + "(";
        result = result + compile_expression(left, scope);
        result = result + ", "
        result = result + compile_expression(right, scope);
        result = result + ")";
    else:
        result = result + compile_expression(left, scope);
        result = result + operator_node.operator;
        result = result + compile_expression(right, scope);

    return result;

def compile_compare(compare_node: lua_ast.CompareNode, scope: Scope) -> str:
    result = initialise_string(compare_node, scope);

    # LEFT [OPERATOR] [COMPARATOR] [OPERATOR] [COMPARATOR]
    # 5    <          6            <          7
    # In Lua:
    # 5 < 6 and 6 < 7
    # i.e
    # Left < Comparator1 and Comparator1 < Comparator2
    # "<" is the operator in this case

    result = result + compile_name(compare_node.left, scope);

    for i in range(0, len(compare_node.comparators)):
        op = compare_node.operators[i];
        comp = compare_node.comparators[i];
        last_comp = compare_node.comparators[-1] or compare_node.left;

        result = result + compile_compoperator(op, last_comp, comp, scope);

    return result;

def compile_statement(statement_node: lua_ast.StatementNode, scope: Scope) -> str:
    if isinstance(statement_node, lua_ast.FunctionNode):
        return compile_function(statement_node, scope);
    elif isinstance(statement_node, lua_ast.IfNode):
        return compile_if(statement_node, scope);

    raise Exception("Unknown statement node type during Lua AST -> Lua compilation " + str(type(statement_node)));

def compile_expression(expression_node: lua_ast.ExpressionNode, scope: Scope) -> str:
    if isinstance(expression_node, lua_ast.NameNode):
        return compile_name(expression_node, scope);
    elif isinstance(expression_node, lua_ast.CompareNode):
        return compile_compare(expression_node, scope);

    raise Exception("Unknown expression node type during Lua AST -> Lua compilation " + str(type(expression_node)));

def compile_lines(nodes: List[lua_ast.Node], scope: Scope):
    result = "";

    for node in nodes:
        if issubclass(type(node), lua_ast.StatementNode):
            return compile_statement(node, scope);
        elif issubclass(type(node), lua_ast.ExpressionNode):
            return compile_expression(node, scope);

        raise Exception("Unknown node type during Lua AST -> Lua compilation " + str(type(node)));
    
    return result;

def compile_module(module_node: py_ast.Module) -> str:
    module_node: lua_ast.ModuleNode = map_module(module_node);

    return compile_lines(module_node.body, top_scope);