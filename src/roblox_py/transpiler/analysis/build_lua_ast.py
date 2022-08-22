# Build a new lua AST from python's AST.

import ast as py_ast
from typing import List

from ..lua_ast import lua_ast_nodes as lua_ast

def map_functiondef(pynode: py_ast.FunctionDef, function_node: lua_ast.FunctionNode | None) -> lua_ast.FunctionNode:
    decorators: List[str] = [];

    for decorator in pynode.decorator_list:
        decorators.append(decorator.id);  # type: ignore

    if pynode.returns is not None:
        return_annotation = pynode.returns

    return lua_ast.FunctionNode(
        pynode.name,
        map_arguments(pynode.args),
        map_statements(pynode.body),
        return_annotation,
        decorators,
        pynode.lineno,
        function_node
    );

def map_arguments(pynode: py_ast.arguments) -> List[lua_ast.ArgNode]:
    arguments: List[lua_ast.ArgNode] = [];

    for arg in pynode.args:
        arguments.append(map_argument(arg));

    return arguments;

def map_assignment(pynode: py_ast.Assign, function_node: lua_ast.FunctionNode | None) -> lua_ast.AssignmentNode:
    return lua_ast.AssignmentNode(
        map_expressions(pynode.targets, function_node), 
        map_expression(pynode.value, function_node),
        pynode.lineno,
        function_node);

def map_if(pynode: py_ast.If, function_node: lua_ast.FunctionNode | None) -> lua_ast.IfNode:
    return lua_ast.IfNode(
        map_expression(pynode.test, function_node),
        map_nodes(pynode.body, function_node),
        map_nodes(pynode.orelse, function_node),
        pynode.lineno,
        function_node);

def map_return(return_node: py_ast.Return, function_node: lua_ast.FunctionNode | None) -> lua_ast.ReturnNode:
    return lua_ast.ReturnNode(
        map_expression(return_node.value, function_node),
        return_node.lineno,
        function_node);

def map_name(name: str, lineno: int, function_node: lua_ast.FunctionNode | None) -> lua_ast.NameNode:
    return lua_ast.NameNode(name, lineno, function_node);

def map_constant(constant: py_ast.Constant, function_node: lua_ast.FunctionNode | None) -> lua_ast.ConstantNode:
    return lua_ast.ConstantNode(constant.value, constant.lineno, function_node);

def map_compareop(op: py_ast.cmpop, function_node: lua_ast.FunctionNode) -> lua_ast.CompareOperatorNode:
    if isinstance(op, py_ast.Eq):
        return lua_ast.CmpOpEqNode(function_node);
    elif isinstance(op, py_ast.NotEq):
        return lua_ast.CmpOpNotEqNode(function_node);
    elif isinstance(op, py_ast.Lt):
        return lua_ast.CmpOpLessNode(function_node);
    elif isinstance(op, py_ast.LtE):
        return lua_ast.CmpOpLessEqNode(function_node);
    elif isinstance(op, py_ast.Gt):
        return lua_ast.CmpOpGreaterNode(function_node);
    elif isinstance(op, py_ast.GtE):
        return lua_ast.CmpOpGreaterEqNode(function_node);
    elif isinstance(op, py_ast.Is):
        return lua_ast.CmpOpIsNode(function_node);
    elif isinstance(op, py_ast.IsNot):
        return lua_ast.CmpOpIsNotNode(function_node);
    elif isinstance(op, py_ast.In):
        return lua_ast.CmpOpInNode(op.lineno, function_node);
    elif isinstance(op, py_ast.NotIn):
        return lua_ast.CmpOpNotInNode(op.lineno, function_node);
    else:
        raise Exception("Unknown compare op " + str(type(op)));

def map_compare(compare_node: py_ast.Compare, function_node: lua_ast.FunctionNode | None) -> lua_ast.CompareNode:
    comparators = [];

    for comparator in compare_node.comparators:	
        comparators.append(map_expression(comparator, function_node));

    compare_ops = [];
    for compare_op in compare_node.ops:
        compare_ops.append(map_compareop(compare_op, function_node));
    
    return lua_ast.CompareNode(
        map_expression(compare_node.left, function_node),
        compare_ops,
        comparators,
        compare_node.lineno,
        function_node);

def map_operator(pynode: py_ast.operator, function_node: lua_ast.FunctionNode) -> lua_ast.OperatorNode:
    if isinstance(pynode, py_ast.Add):
        return lua_ast.AddNode(function_node);
    elif isinstance(pynode, py_ast.Sub):
        return lua_ast.SubNode(function_node);
    elif isinstance(pynode, py_ast.Mult):
        return lua_ast.MultNode(function_node);
    elif isinstance(pynode, py_ast.Div):
        return lua_ast.DivNode(function_node);
    elif isinstance(pynode, py_ast.Mod):
        return lua_ast.ModNode(function_node);
    elif isinstance(pynode, py_ast.Pow):
        return lua_ast.PowNode(function_node);
    elif isinstance(pynode, py_ast.LShift):
        return lua_ast.LShiftNode(function_node);
    elif isinstance(pynode, py_ast.RShift):
        return lua_ast.RShiftNode(function_node);
    elif isinstance(pynode, py_ast.BitOr):
        return lua_ast.BitOrNode(function_node);
    elif isinstance(pynode, py_ast.BitXor):
        return lua_ast.BitXorNode(function_node);
    elif isinstance(pynode, py_ast.BitAnd):
        return lua_ast.BitAndNode(function_node);
    elif isinstance(pynode, py_ast.FloorDiv):
        return lua_ast.FloorDivNode(function_node);

def map_binop(pynode: py_ast.BinOp, function_node: lua_ast.FunctionNode) -> lua_ast.BinOpNode:
    return lua_ast.BinOpNode(
        map_expression(pynode.left, function_node),
        map_expression(pynode.right, function_node),
        map_operator(pynode.op, function_node),
        pynode.lineno,
        function_node);

def map_argument(pynode: py_ast.arg) -> lua_ast.ArgNode:
    return lua_ast.ArgNode(
        pynode.arg,
        pynode.annotation,
        pynode.lineno);

def map_call(call_node: py_ast.Call, attributed_to: lua_ast.Node | None, function_node: lua_ast.FunctionNode) -> lua_ast.CallNode:
    return lua_ast.CallNode(
        map_expression(call_node.func, function_node),
        map_expressions(call_node.args, function_node),
        call_node.lineno,
        function_node
    )

# Selector function
def map_expression(expression: py_ast.expr, function_node: lua_ast.FunctionNode) -> lua_ast.ExpressionNode:
    if isinstance(expression, py_ast.Name):
        return map_name(expression.id, expression.lineno, function_node);
    elif isinstance(expression, py_ast.Compare):
        return map_compare(expression, function_node);
    elif isinstance(expression, py_ast.Constant):
        return map_constant(expression, function_node);
    elif isinstance(expression, py_ast.BinOp):
        return map_binop(expression, function_node);
    elif isinstance(expression, py_ast.Call):
        return map_call(expression, None, function_node);

    raise Exception("Unknown expression type " + str(type(expression)));

# Selector function
def map_statement(statement: py_ast.stmt, function_node: lua_ast.FunctionNode | None) -> lua_ast.StatementNode:
    if isinstance(statement, py_ast.FunctionDef):
        return map_functiondef(statement, function_node);
    elif isinstance(statement, py_ast.Assign):
        return map_assignment(statement, function_node);
    elif isinstance(statement, py_ast.If):
        return map_if(statement, function_node);
    elif isinstance(statement, py_ast.Return):
        return map_return(statement, function_node);
    elif isinstance(statement, py_ast.Expr):
        return map_expression(statement.value, function_node);
    
    raise Exception("Unknown statement type " + str(type(statement)));

# Looper
def map_expressions(expressions: List[py_ast.expr], function_node: lua_ast.FunctionNode | None) -> List[lua_ast.ExpressionNode]:
    result = [];

    for expression in expressions:
        result.append(map_expression(expression, function_node));

    return result;

# Looper
def map_statements(statements: List[py_ast.stmt], function_node: lua_ast.FunctionNode | None) -> List[lua_ast.StatementNode]:
    result = [];

    for statement in statements:
        result.append(map_statement(statement, function_node))
    
    return result;

# Looper
def map_nodes(nodes: List[py_ast.stmt], function_node: lua_ast.FunctionNode | None) -> List[lua_ast.Node]:
    result = []

    for node in nodes:
        if isinstance(node, py_ast.stmt):
            result.append(map_statement(node, function_node));
        elif isinstance(node, py_ast.expr):
            result.append(map_expression(node, function_node));
        else:
            raise Exception("Unknown node type " + str(type(node)));
        
    return result;

def map_module(module: py_ast.Module) -> lua_ast.ModuleNode:
    return lua_ast.ModuleNode(map_nodes(module.body, None))