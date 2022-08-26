# Build a new lua AST from python's AST.

from __future__ import annotations
import ast as py_ast
from typing import Dict, List

from ..lua_ast import lua_ast_nodes as lua_ast

from ..scope import LuaScope

script_options: List[str] = [
    "@ropy:ignore_table_offset"
]

def map_functiondef(pynode: py_ast.FunctionDef, scope: LuaScope) -> lua_ast.FunctionNode:
    decorators: List[str] = [];

    for decorator in pynode.decorator_list:
        decorators.append(decorator.id);  # type: ignore
    
    new_scope = scope.add_child(None);
    
    new_function_node = lua_ast.FunctionNode(
        pynode.name,
        [],
        [],
        decorators,
        None,
        False,
        [],
        [],
        pynode.lineno,
    );

    scope.functions.append(new_function_node);
    
    new_scope.node = new_function_node;

    new_function_node.scope = scope;

    return_annotation: lua_ast.ExpressionNode | None = None;

    if pynode.returns is not None:
        return_annotation = map_expression(pynode.returns, new_scope);

    new_function_node.return_annotation = return_annotation;
    new_function_node.args = map_arguments(pynode.args, new_scope);
    new_function_node.body = map_statements(pynode.body, new_scope);

    return new_function_node;

def map_arguments(pynode: py_ast.arguments, scope: LuaScope) -> List[lua_ast.ArgNode]:
    arguments: List[lua_ast.ArgNode] = [];

    for arg in pynode.args:
        arguments.append(map_argument(arg, scope));

    return arguments;

def map_assignment(pynode: py_ast.Assign, scope: LuaScope) -> lua_ast.AssignmentNode:
    # Loop through targets
    for target in pynode.targets:
        if not isinstance(target, py_ast.Name):
            continue;
        
        function_scope = scope.get_function_scope()
        direct = function_scope == scope

        function_scope.add_variable(lua_ast.Variable(target.id, "nil", direct, target.lineno));
        
    assignment_node = lua_ast.AssignmentNode(
        map_expressions(pynode.targets, scope), 
        map_expression(pynode.value, scope),
        pynode.lineno);

    assignment_node.scope = scope;

    return assignment_node;

def map_if(pynode: py_ast.If, scope: LuaScope) -> lua_ast.IfNode:
    new_scope = scope.add_child(None);

    current_node = pynode;

    if_node = lua_ast.IfNode(
        map_expression(pynode.test, new_scope),
        map_statements(pynode.body, new_scope),
        [],
        [],
        pynode.lineno,
    );

    if len(current_node.orelse) > 0 and not isinstance(pynode.orelse[0], py_ast.If):
        new_new_scope = scope.add_child(if_node);
        if_node.elsebody = map_statements(pynode.orelse, new_new_scope);

    new_scope.node = if_node;
    if_node.scope = scope;

    while True:
        if len(current_node.orelse) == 0: break;

        if not isinstance(current_node.orelse[0], py_ast.If):
            break;
        
        current_node = current_node.orelse[0];

        newer_scope = scope.add_child(None);
        
        elseif_node = lua_ast.ElseIfNode(
            map_expression(current_node.test, newer_scope),
            map_statements(current_node.body, newer_scope),
            map_statements(current_node.orelse, newer_scope),
            current_node.lineno
        );

        newer_scope.node = elseif_node;
        elseif_node.scope = scope;
        if_node.elseifbody.append(elseif_node);

    return if_node;

def map_return(pynode: py_ast.Return, scope: LuaScope) -> lua_ast.ReturnNode:
    returns: lua_ast.ExpressionNode | None = None;

    if pynode.value is not None:
        returns = map_expression(pynode.value, scope);
    else:
        returns = None;

    return_node = lua_ast.ReturnNode(returns, pynode.lineno);
    return_node.scope = scope;
    
    return return_node;

def map_name(pynode: py_ast.Name, scope: LuaScope) -> lua_ast.NameNode:
    name_node = lua_ast.NameNode(pynode.id, pynode.lineno);
    name_node.scope = scope;

    return name_node;

def map_constant(pynode: py_ast.Constant, scope: LuaScope) -> lua_ast.ConstantNode:
    type = "nil";

    # Check if value is int or float
    if isinstance(pynode.value, int) or isinstance(pynode.value, float):
        type = "number";

    # Check if value is None
    elif pynode.value is None:
        pynode.value = "nil";
        type = "nil";

    # Check if value is a boolean
    elif pynode.value == "True" or pynode.value == "False":
        pynode.value = "true" if pynode.value == "True" else "false";
        type = "boolean";

    # Check if value is a string (i.e begins and ends with ')
    else:
        type = "string";
        if pynode.value in script_options:
            scope.apply_option(pynode.value);

    constant_node = lua_ast.ConstantNode(pynode.value, type, pynode.lineno);
    constant_node.scope = scope;

    return constant_node

def map_compareop(pynode: py_ast.cmpop, scope: LuaScope) -> lua_ast.CompareOperatorNode:
    new_node: lua_ast.CompareOperatorNode;

    if isinstance(pynode, py_ast.Eq):
        new_node = lua_ast.CmpOpEqNode();
    elif isinstance(pynode, py_ast.NotEq):
        new_node = lua_ast.CmpOpNotEqNode();
    elif isinstance(pynode, py_ast.Lt):
        new_node = lua_ast.CmpOpLessNode();
    elif isinstance(pynode, py_ast.LtE):
        new_node = lua_ast.CmpOpLessEqNode();
    elif isinstance(pynode, py_ast.Gt):
        new_node = lua_ast.CmpOpGreaterNode();
    elif isinstance(pynode, py_ast.GtE):
        new_node = lua_ast.CmpOpGreaterEqNode();
    elif isinstance(pynode, py_ast.Is):
        new_node = lua_ast.CmpOpIsNode();
    elif isinstance(pynode, py_ast.IsNot):
        new_node = lua_ast.CmpOpIsNotNode();
    elif isinstance(pynode, py_ast.In):
        new_node = lua_ast.CmpOpInNode();
    elif isinstance(pynode, py_ast.NotIn):
        new_node = lua_ast.CmpOpNotInNode();
    else:
        raise Exception("Unknown compare op " + str(type(pynode)));
    
    new_node.scope = scope;
    
    return new_node;

def map_compare(pynode: py_ast.Compare, scope: LuaScope) -> lua_ast.CompareNode:
    comparators: List[lua_ast.ExpressionNode] = [];

    for comparator in pynode.comparators:	
        comparators.append(map_expression(comparator, scope));

    operators: List[lua_ast.CompareOperatorNode] = [];

    for operator in pynode.ops:
        operators.append(map_compareop(operator, scope));

    new_node = lua_ast.CompareNode(
        map_expression(pynode.left, scope),
        operators,
        comparators,
        pynode.lineno);

    new_node.scope = scope;
    
    return new_node

def map_operator(pynode: py_ast.operator, scope: LuaScope) -> lua_ast.OperatorNode:
    if isinstance(pynode, py_ast.Add):
        return lua_ast.AddNode();
    elif isinstance(pynode, py_ast.Sub):
        return lua_ast.SubNode();
    elif isinstance(pynode, py_ast.Mult):
        return lua_ast.MultNode();
    elif isinstance(pynode, py_ast.Div):
        return lua_ast.DivNode();
    elif isinstance(pynode, py_ast.Mod):
        return lua_ast.ModNode();
    elif isinstance(pynode, py_ast.Pow):
        return lua_ast.PowNode();
    elif isinstance(pynode, py_ast.LShift):
        return lua_ast.LShiftNode();
    elif isinstance(pynode, py_ast.RShift):
        return lua_ast.RShiftNode();
    elif isinstance(pynode, py_ast.BitOr):
        return lua_ast.BitOrNode();
    elif isinstance(pynode, py_ast.BitXor):
        return lua_ast.BitXorNode();
    elif isinstance(pynode, py_ast.BitAnd):
        return lua_ast.BitAndNode();
    elif isinstance(pynode, py_ast.FloorDiv):
        return lua_ast.FloorDivNode();
    
    raise Exception("Unknown operator " + str(type(pynode)));

def map_binop(pynode: py_ast.BinOp, scope: LuaScope) -> lua_ast.BinOpNode:
    new_node = lua_ast.BinOpNode(
        map_expression(pynode.left, scope),
        map_expression(pynode.right, scope),
        map_operator(pynode.op, scope),
        pynode.lineno);

    new_node.scope = scope;

    return new_node

def map_argument(pynode: py_ast.arg, scope: LuaScope) -> lua_ast.ArgNode:
    annotation: lua_ast.ExpressionNode | None = None;

    if pynode.annotation is not None:
        annotation = map_expression(pynode.annotation, scope);
    
    return lua_ast.ArgNode(
        pynode.arg,
        annotation,
        pynode.lineno);

def map_call(pynode: py_ast.Call, attributed_to: lua_ast.Node | None, scope: LuaScope) -> lua_ast.CallNode:
    # get the FunctionNode by looping through the scope
    # and finding the function that is called by pynode.func.name
    call_node: lua_ast.CallNode = lua_ast.CallNode(
        map_expression(pynode.func, scope),
        map_expressions(pynode.args, scope),
        attributed_to,
        pynode.lineno)

    call_node.scope = scope;

    return call_node;

def map_slice(pynode: py_ast.Slice, subscript: lua_ast.SubscriptNode, scope: LuaScope) -> lua_ast.SliceNode:
    lower: lua_ast.ExpressionNode | None = None;
    upper: lua_ast.ExpressionNode | None = None;
    step: lua_ast.ExpressionNode | None = None;

    if pynode.lower is not None:
        lower = map_expression(pynode.lower, scope);
    
    if pynode.upper is not None:
        upper = map_expression(pynode.upper, scope);
    
    if pynode.step is not None:
        step = map_expression(pynode.step, scope);
    
    return lua_ast.SliceNode(subscript, lower, upper, step, pynode.lineno, );

def map_dict(pynode: py_ast.Dict, scope: LuaScope) -> lua_ast.TableNode:
    keys: List[lua_ast.ExpressionNode] = [];

    for key in pynode.keys:
        if key is not None:
            keys.append(map_expression(key, scope));

    values = map_expressions(pynode.values, scope);

    new_node = lua_ast.TableNode(
        keys,
        values,
        "dict",
        pynode.lineno
    );

    new_node.scope = scope;
    
    return new_node;

def map_list(pynode: py_ast.List, scope: LuaScope) -> lua_ast.TableNode:
    result: Dict[lua_ast.ExpressionNode, lua_ast.ExpressionNode] = {};

    for index, value in enumerate(pynode.elts):
        constant_node = lua_ast.ConstantNode(index, "number", pynode.lineno)
        constant_node.scope = scope;
        result[constant_node] = map_expression(value, scope);

    # keys
    keys = list(result.keys());

    # values
    values = list(result.values());

    new_node = lua_ast.TableNode(keys, values, "list", pynode.lineno);
    new_node.scope = scope;

    return new_node

def map_subscript(pynode: py_ast.Subscript, scope: LuaScope) -> lua_ast.SubscriptNode:
    new_subscript_node = lua_ast.SubscriptNode(
        map_expression(pynode.value, scope),
        None,
        pynode.lineno)
    
    if isinstance(pynode.slice, py_ast.BinOp):
        new_subscript_node.slice = map_binop(pynode.slice, scope);
    elif isinstance(pynode.slice, py_ast.Slice):
        new_subscript_node.slice = map_slice(pynode.slice, new_subscript_node, scope);
    elif isinstance(pynode.slice, py_ast.Name):
        new_subscript_node.slice = map_name(pynode.slice, scope);
    else:
        raise Exception("Unknown slice type " + str(type(pynode.slice)));
    
    new_subscript_node.scope = scope;

    return new_subscript_node;

def map_while(pynode: py_ast.While, scope: LuaScope) -> lua_ast.WhileNode:
    new_scope = scope.add_child(None);
    
    while_node = lua_ast.WhileNode(
        map_expression(pynode.test, new_scope),
        map_nodes(pynode.body, new_scope),
        pynode.lineno);

    new_scope.node = while_node;

    while_node.scope = scope;

    return while_node;

def map_yield(pynode: py_ast.Yield, scope: LuaScope) -> lua_ast.YieldNode:
    value = None;
    
    if pynode.value is not None:
        value = map_expression(pynode.value, scope)

    yield_node = lua_ast.YieldNode(
        value,
        pynode.lineno);

    yield_node.scope = scope;

    function_scope = scope.get_function_scope()

    if function_scope.node is not None:
        function_scope.node.yields.append(value);
    
    return yield_node;

def map_for(pynode: py_ast.For, scope: LuaScope) -> lua_ast.ForNode:
    new_scope = scope.add_child(None);

    for_node = lua_ast.ForNode(
        map_expression(pynode.target, new_scope),
        map_expression(pynode.iter, new_scope),
        map_nodes(pynode.body, new_scope),
        pynode.lineno
    );

    for_node.scope = scope;
    new_scope.node = for_node;

    return for_node

def map_attribute(pynode: py_ast.Attribute, scope: LuaScope) -> lua_ast.AttributeNode:
    new_node = lua_ast.AttributeNode(
        map_expression(pynode.value, scope),
        pynode.attr,
        pynode.lineno
    );
    new_node.scope = scope;

    return new_node

def map_delete(pynode: py_ast.Delete, scope: LuaScope) -> lua_ast.DeleteNode:
    delete_node = lua_ast.DeleteNode(
        map_expressions(pynode.targets, scope),
        pynode.lineno
    );
    delete_node.scope = scope;

    return delete_node

def map_augmentedassignment(pynode: py_ast.AugAssign, scope: LuaScope) -> lua_ast.AugmentedAssignmentNode:
    augmentedassignment_node = lua_ast.AugmentedAssignmentNode(
        map_expression(pynode.target, scope),
        map_operator(pynode.op, scope),
        map_expression(pynode.value, scope),
        pynode.lineno
    );

    augmentedassignment_node.scope = scope;
    
    return augmentedassignment_node

def map_comprehension(pynode: py_ast.comprehension, scope: LuaScope) -> lua_ast.ComprehensionNode:
    line = None;
    if hasattr(pynode, "lineno"):
        line = pynode.lineno;
    
    comprehension_node = lua_ast.ComprehensionNode(
        map_expression(pynode.target, scope),
        map_expression(pynode.iter, scope),
        map_expressions(pynode.ifs, scope),
        line
    );

    comprehension_node.scope = scope;

    return comprehension_node

def map_listcomp(pynode: py_ast.ListComp, scope: LuaScope) -> lua_ast.ListCompNode:
    generators: List[lua_ast.ComprehensionNode] = [];

    for generator in pynode.generators:
        generators.append(map_comprehension(generator, scope));

    new_node = lua_ast.ListCompNode(
        map_expression(pynode.elt, scope),
        generators,
        pynode.lineno
    );

    new_node.scope = scope;

    return new_node

def map_generatorexp(pynode: py_ast.GeneratorExp, scope: LuaScope) -> lua_ast.GeneratorExpNode:
    generators: List[lua_ast.ComprehensionNode] = [];

    for generator in pynode.generators:
        generators.append(map_comprehension(generator, scope));

    new_node = lua_ast.GeneratorExpNode(
        map_expression(pynode.elt, scope),
        generators,
        pynode.lineno
    );

    new_node.scope = scope;

    return new_node

def map_starred(pynode: py_ast.Starred, scope: LuaScope) -> lua_ast.StarredNode:
    new_node = lua_ast.StarredNode(
        map_expression(pynode.value, scope),
        pynode.lineno
    );

    new_node.scope = scope;

    return new_node

# Selector function
def map_expression(expression: py_ast.expr, scope: LuaScope) -> lua_ast.ExpressionNode:
    if isinstance(expression, py_ast.Name):
        return map_name(expression, scope);
    elif isinstance(expression, py_ast.Compare):
        return map_compare(expression, scope);
    elif isinstance(expression, py_ast.Constant):
        return map_constant(expression, scope);
    elif isinstance(expression, py_ast.BinOp):
        return map_binop(expression, scope);
    elif isinstance(expression, py_ast.Call):
        return map_call(expression, None, scope);
    elif isinstance(expression, py_ast.Subscript):
        return map_subscript(expression, scope);
    elif isinstance(expression, py_ast.Dict):
        return map_dict(expression, scope);
    elif isinstance(expression, py_ast.Yield):
        return map_yield(expression, scope);
    elif isinstance(expression, py_ast.List):
        return map_list(expression, scope);
    elif isinstance(expression, py_ast.Attribute):
        return map_attribute(expression, scope);
    elif isinstance(expression, py_ast.ListComp):
        return map_listcomp(expression, scope);
    elif isinstance(expression, py_ast.GeneratorExp):
        return map_generatorexp(expression, scope);
    elif isinstance(expression, py_ast.Starred):
        return map_starred(expression, scope);

    raise Exception("Unknown expression type " + str(type(expression)));

# Selector function
def map_statement(statement: py_ast.stmt, scope: LuaScope) -> lua_ast.StatementNode | lua_ast.ExpressionNode:
    if isinstance(statement, py_ast.FunctionDef):
        return map_functiondef(statement, scope);
    elif isinstance(statement, py_ast.Assign):
        return map_assignment(statement, scope);
    elif isinstance(statement, py_ast.If):
        return map_if(statement, scope);
    elif isinstance(statement, py_ast.Return):
        return map_return(statement, scope);
    elif isinstance(statement, py_ast.Expr):
        return map_expression(statement.value, scope);
    elif isinstance(statement, py_ast.While):
        return map_while(statement, scope);
    elif isinstance(statement, py_ast.For):
        return map_for(statement, scope);
    elif isinstance(statement, py_ast.Delete):
        return map_delete(statement, scope);
    elif isinstance(statement, py_ast.AugAssign):
        return map_augmentedassignment(statement, scope);
    
    raise Exception("Unknown statement type " + str(type(statement)));

# Looper
def map_expressions(expressions: List[py_ast.expr], scope: LuaScope) -> List[lua_ast.ExpressionNode]:
    result: List[lua_ast.ExpressionNode] = [];

    for expression in expressions:
        result.append(map_expression(expression, scope));

    return result;

# Looper
def map_statements(statements: List[py_ast.stmt], scope: LuaScope) -> List[lua_ast.Node]:
    result: List[lua_ast.Node] = [];

    for statement in statements:
        result.append(map_statement(statement, scope))
    
    return result;

# Looper
def map_nodes(nodes: List[py_ast.stmt] | List[py_ast.expr] | List[py_ast.arg],
              scope: LuaScope) -> List[lua_ast.Node]:

    result: List[lua_ast.Node] = []

    for node in nodes:
        if isinstance(node, py_ast.stmt):
            result.append(map_statement(node, scope))
        elif isinstance(node, py_ast.expr):
            result.append(map_expression(node, scope))
        else:
            raise Exception("Unknown node type " + str(type(node)));
            
    return result;

def map_module(module: py_ast.Module) -> lua_ast.ModuleNode:
    top_scope = LuaScope("0", None)
    mapped_nodes = map_nodes(module.body, top_scope);
    final = lua_ast.ModuleNode(mapped_nodes)

    return final;