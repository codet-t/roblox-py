from typing import Dict, List

import ast as py_ast;

from ..analysis.build_lua_ast import map_module
from ..lua_ast import lua_ast_nodes as lua_ast
from ..lua_ast.lua_scope import Scope

top_scope = Scope("0", "top", [], [], None)

options: Dict[str, bool] = {
    "toggle_ast": False,
    "toggle_scope_ids": False,
    "toggle_lines": False
}

def initialise_string(node: lua_ast.Node, scope: Scope) -> str:
    result: str = "";

    if options["toggle_ast"]:
        result = result + "--[[" + node.__class__.__name__ + "]]"

    if options["toggle_scope_ids"]:
        result = result + "--[[ ScopeId: " + scope.scope_id + "]]";
    
    return result;

def compile_if(if_node: lua_ast.IfNode, scope: Scope):
    result = initialise_string(if_node, scope);

    new_scope = scope.add_child("if", if_node);

    result = result + "if " + compile_expression(if_node.condition, scope) + " then\n";
    result = result + compile_lines(if_node.body, new_scope);

    if if_node.else_body is not None:
        result = result + scope.get_offset() + "else\n";
        result = result + compile_lines(if_node.else_body, new_scope);

    result = result + scope.get_offset() + "end";

    return result;

def compile_function(function_node: lua_ast.FunctionNode, scope: Scope) -> str:
    result: str = initialise_string(function_node, scope);

    anonymous = function_node.name is None;

    new_scope: Scope;

    if anonymous and not function_node.is_lambda:
        new_scope = scope.add_child("anonymous_function", function_node);
    else:
        new_scope = scope.add_child("function", function_node);


    result = result + "function"
    if function_node.name is None:
        result = result + "(";
    else:
        result = result + " " + function_node.name + "(";

    for arg in function_node.args:
        result = result + arg.identifier
        if arg != function_node.args[-1]:
            result = result + ", ";

    result = result + ")\n";

    result = result + compile_lines(function_node.body, new_scope);
    result = result + "end";

    return result;

def compile_name(name_node: lua_ast.NameNode, scope: Scope) -> str:
    result = initialise_string(name_node, scope);

    result = result + name_node.name;

    return result;

def compile_constant(constant_node: lua_ast.ConstantNode, scope: Scope) -> str:
    result = initialise_string(constant_node, scope);

    result = result + constant_node.value;

    return result;

def compile_compoperator(operator_node: lua_ast.CompareOperatorNode, left: lua_ast.ExpressionNode, right: lua_ast.ExpressionNode, scope: Scope) -> str:
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
        result = result + " " + operator_node.operator + " ";
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

    for i in range(0, len(compare_node.comparators)):
        op = compare_node.operators[i];
        comp = compare_node.comparators[i];
        last_comp = compare_node.left
        if i > 0:
            last_comp = compare_node.comparators[i - 1];

        result = result + compile_compoperator(op, last_comp, comp, scope);

    return result;

def compile_return(return_node: lua_ast.ReturnNode, scope: Scope) -> str:
    result = initialise_string(return_node, scope);

    result = result + "return ";

    if return_node.value is not None:
        result = result + compile_expression(return_node.value, scope);
    else:
        result = result + "nil";

    return result;

def compile_call(call_node: lua_ast.CallNode, scope: Scope) -> str:
    result = initialise_string(call_node, scope);

    result = result + compile_expression(call_node.value, scope);
    result = result + "(";

    for arg in call_node.args:
        result = result + compile_expression(arg, scope);
        if arg != call_node.args[-1]:
            result = result + ", ";
    
    result = result + ")";

    return result;

def compile_subscript(subscript_node: lua_ast.SubscriptNode, scope: Scope) -> str:
    result = initialise_string(subscript_node, scope);

    # If slice.lower is => 0, and slice.upper&step is None, then it is a normal subscript
    # That is to say, value[slice.lower] is OK
    lower = compile_expression(subscript_node.slice.lower, scope)

    if lower.isnumeric() and int(lower) >= 0 and subscript_node.slice.upper is None and subscript_node.slice.step is None:
        result = result + compile_expression(subscript_node.value, scope);
        result = result + "[" + compile_expression(subscript_node.slice.lower, scope) + "]";
    else:
        # We need to use the ropy.slice function
        upper = compile_expression(subscript_node.slice.upper, scope) if subscript_node.slice.upper is not None else "nil";
        step = compile_expression(subscript_node.slice.step, scope) if subscript_node.slice.step is not None else "nil";

        result = result + "roblox.slice(";
        result = result + compile_expression(subscript_node.value, scope);
        result = result + ", " + lower + ", " + upper + ", " + step + ")";

    return result;

def compile_operator(operator_node: lua_ast.OperatorNode, left: lua_ast.ExpressionNode, right: lua_ast.ExpressionNode, scope: Scope) -> str:
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
        result = result + " " + operator_node.operator + " ";
        result = result + compile_expression(right, scope);
    
    return result;

def compile_binop(binop_node: lua_ast.BinOpNode, scope: Scope) -> str:
    result = initialise_string(binop_node, scope);

    result = result + compile_operator(binop_node.operator, binop_node.left, binop_node.right, scope);
    
    return result;

def compile_statement(statement_node: lua_ast.StatementNode, scope: Scope) -> str:
    if isinstance(statement_node, lua_ast.FunctionNode):
        return compile_function(statement_node, scope);
    elif isinstance(statement_node, lua_ast.IfNode):
        return compile_if(statement_node, scope)
    elif isinstance(statement_node, lua_ast.ReturnNode):
        return compile_return(statement_node, scope)
    elif isinstance(statement_node, lua_ast.CallNode):
        return compile_call(statement_node, scope)

    raise Exception("Unknown statement node type during Lua AST -> Lua compilation " + str(type(statement_node)));

def compile_expression(expression_node: lua_ast.ExpressionNode, scope: Scope) -> str:
    if isinstance(expression_node, lua_ast.NameNode):
        return compile_name(expression_node, scope);
    elif isinstance(expression_node, lua_ast.CompareNode):
        return compile_compare(expression_node, scope);
    elif isinstance(expression_node, lua_ast.ConstantNode):
        return compile_constant(expression_node, scope);
    elif isinstance(expression_node, lua_ast.SubscriptNode):
        return compile_subscript(expression_node, scope);
    elif isinstance(expression_node, lua_ast.BinOpNode):
        return compile_binop(expression_node, scope);
    elif isinstance(expression_node, lua_ast.CallNode):
        return compile_call(expression_node, scope);

    raise Exception("Unknown expression node type during Lua AST -> Lua compilation " + str(type(expression_node)));

def compile_line(node: lua_ast.Node, scope: Scope) -> str:
    result = "";

    if issubclass(type(node), lua_ast.StatementNode):
        result = result + compile_statement(node, scope);  # type: ignore
    elif issubclass(type(node), lua_ast.ExpressionNode):
        result = result + compile_expression(node, scope);  # type: ignore
    else:
        raise Exception("Unknown node type during Lua AST -> Lua compilation " + str(type(node)));

    result = scope.get_offset() + result;

    if options["toggle_lines"]:
        result = result + "--" + str(node.line_begin)
    
    result = result + "\n";

    return result;

def compile_lines(nodes: List[lua_ast.Node], scope: Scope) -> str:
    result = "";

    for node in nodes:
        result = result + compile_line(node, scope);

    return result;
    
def compile_module(module_node: py_ast.Module) -> str:
    prefix = "-- Compiled with roblox-py:\n-- https://github.com/codetariat/roblox-py\n"

    return prefix + compile_lines(map_module(module_node).body, top_scope);