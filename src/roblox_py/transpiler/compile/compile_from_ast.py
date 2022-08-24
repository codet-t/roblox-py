from typing import Dict, List

import ast as py_ast;

from ..analysis.build_lua_ast import map_module
from ..lua_ast import lua_ast_nodes as lua_ast

options: Dict[str, bool] = {
    "toggle_ast": False,
    "toggle_scope_ids": False,
    "toggle_lines": False
}

def initialise_string(node: lua_ast.Node) -> str:
    result: str = "";

    if options["toggle_ast"]:
        result = result + "--[[" + node.__class__.__name__ + "]]"

    if options["toggle_scope_ids"]:
        result = result + "--[[ ScopeId: " + node.scope.scope_id + "]]";
    
    return result;

def compile_if(if_node: lua_ast.IfNode):
    result = initialise_string(if_node);

    result = result + "if " + compile_expression(if_node.condition) + " then\n";
    result = result + compile_lines(if_node.body);

    if if_node.else_body is not None:
        result = result + if_node.scope.get_offset() + "else\n";
        result = result + compile_lines(if_node.else_body);

    result = result + if_node.scope.get_offset() + "end";

    return result;

def compile_function(function_node: lua_ast.FunctionNode) -> str:
    result: str = initialise_string(function_node);

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

    if len(function_node.yields) > 0:
        # we have to do offset=1 because yield is technically part of the function_node itself
        result = result + function_node.scope.get_offset(1) + "local yield = {};\n";

    result = result + compile_lines(function_node.body);
    result = result + function_node.scope.get_offset() + "end";
    
    if function_node.scope.scope_id == "0":
        result = result + "\n";

    return result;

def compile_name(name_node: lua_ast.NameNode) -> str:
    result = initialise_string(name_node);

    result = result + name_node.name;

    return result;

def compile_constant(constant_node: lua_ast.ConstantNode) -> str:
    result = initialise_string(constant_node);

    if constant_node.type == "string":
        result = result + "\"" + constant_node.value + "\"";
    else:
        result = result + constant_node.value;

    return result;

def compile_compoperator(operator_node: lua_ast.CompareOperatorNode, left: lua_ast.ExpressionNode, right: lua_ast.ExpressionNode) -> str:
    result = initialise_string(operator_node);

    if operator_node.parenthesis:
        result = result + operator_node.operator
        result = result + "(";
        result = result + compile_expression(left);
        result = result + ", "
        result = result + compile_expression(right);
        result = result + ")";
    else:
        result = result + compile_expression(left);
        result = result + " " + operator_node.operator + " ";
        result = result + compile_expression(right);
    
    return result;

def compile_compare(compare_node: lua_ast.CompareNode) -> str:
    result = initialise_string(compare_node);

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

        result = result + compile_compoperator(op, last_comp, comp);

    return result;

def compile_return(return_node: lua_ast.ReturnNode) -> str:
    result = initialise_string(return_node);

    result = result + "return ";

    if return_node.value is not None:
        result = result + compile_expression(return_node.value);
    else:
        result = result + "nil";

    return result;

def compile_call(call_node: lua_ast.CallNode) -> str:
    result = initialise_string(call_node);

    result = result + compile_expression(call_node.value);
    result = result + "(";

    for arg in call_node.args:
        result = result + compile_expression(arg);
        if arg != call_node.args[-1]:
            result = result + ", ";
    
    result = result + ")";

    return result;

def compile_subscript(subscript_node: lua_ast.SubscriptNode) -> str:
    result = initialise_string(subscript_node);

    if isinstance(subscript_node.value, lua_ast.BinOpNode):
        result = result + compile_expression(subscript_node.value);
    elif isinstance(subscript_node.value, lua_ast.SliceNode):
        # If slice.lower is => 0, and slice.upper&step is None, then it is a normal subscript
        # That is to say, value[slice.lower] is OK
        lower = compile_expression(subscript_node.slice.lower)

        if lower.isnumeric() and int(lower) >= 0 and subscript_node.slice.upper is None and subscript_node.slice.step is None:
            result = result + compile_expression(subscript_node.value);
            result = result + "[" + compile_expression(subscript_node.slice.lower) + "]";
        else:
            # We need to use the ropy.slice function
            upper = compile_expression(subscript_node.slice.upper) if subscript_node.slice.upper is not None else "nil";
            step = compile_expression(subscript_node.slice.step) if subscript_node.slice.step is not None else "nil";

            result = result + "roblox.slice(";
            result = result + compile_expression(subscript_node.value);
            result = result + ", " + lower + ", " + upper + ", " + step + ")";
    elif isinstance(subscript_node.value, lua_ast.NameNode):
        result = result + compile_expression(subscript_node.value);
    else:
        raise Exception("Unknown subscript value type: " + str(type(subscript_node.value)));

    return result;

def compile_binop(binop_node: lua_ast.BinOpNode) -> str:
    result = initialise_string(binop_node);

    parenthesis = binop_node.operator.parenthesis;

    if parenthesis:
        result = result + binop_node.operator.value + "(";
        result = result + compile_expression(binop_node.left);
        result = result + ", ";
        result = result + compile_expression(binop_node.right);
        result = result + ")";
    else:
        result = result + compile_expression(binop_node.left);
        result = result + " " + binop_node.operator.value + " ";
        result = result + compile_expression(binop_node.right);
    
    return result;

def compile_assignment(assignment_node: lua_ast.AssignmentNode) -> str:
    result = initialise_string(assignment_node);

    # Only one value is allowed in an assignment
    # But multiple targets...

    # Target1 = Value1; Target2 = Value1; Target3 = Value1; etc...
    value = compile_expression(assignment_node.value);

    function_scope = assignment_node.scope.get_function();

    for i in range(0, len(assignment_node.targets)):
        target = assignment_node.targets[i];
        if isinstance(target, lua_ast.NameNode):
            for v in function_scope.variables:
                if v.name == target.name and not v.administred:
                    result = result + "local ";
                    v.administred = True;
                    break;

        result = result + compile_expression(target);
        result = result + " = ";
        result = result + value

        if i < len(assignment_node.targets) - 1:
            result = result + "; ";
    
    return result;

def compile_table(table_node: lua_ast.TableNode) -> str:
    result = initialise_string(table_node);

    result = result + "{";
    for i in range(0, len(table_node.keys)):
        key = table_node.keys[i];
        value = table_node.values[i];
        # key = value
        result = result + "[" + compile_expression(key) + "] = ";
        result = result + compile_expression(value);
        if i < len(table_node.keys) - 1:
            result = result + ", ";
    result = result + "}";

    return result;

def compile_while(node: lua_ast.WhileNode) -> str:
    result = initialise_string(node);

    result = result + "while ";
    result = result + compile_expression(node.condition);
    result = result + " do\n";
    result = result + compile_lines(node.body);
    result = result + node.scope.get_offset() + "end";

    return result;

def compile_yield(yield_node: lua_ast.YieldNode) -> str:
    result = initialise_string(yield_node);

    value = "nil"

    if yield_node.value is not None:
        value = compile_expression(yield_node.value);

    result = result + "table.insert(yield, "
    result = result + value
    result = result + ")";

    return result;

def compile_for(node: lua_ast.ForNode) -> str:
    result = initialise_string(node);

    result = result + "for ";
    result = result + compile_expression(node.target);
    result = result + " in ";
    result = result + compile_expression(node.iterable);
    result = result + " do\n";
    result = result + compile_lines(node.body);
    result = result + node.scope.get_offset() + "end";

    return result;

def compile_attribute(attribute_node: lua_ast.AttributeNode) -> str:
    result = initialise_string(attribute_node);

    result = result + compile_expression(attribute_node.value);
    result = result + "." + attribute_node.attribute;
    
    return result;

def compile_delete(delete_node: lua_ast.DeleteNode) -> str:
    result = initialise_string(delete_node);

    # target1 = nil; target2 = nil; target3 = nil; etc...
    # or:
    # target1, target2, target3 = nil, nil, nil; etc...

    for i in range(0, len(delete_node.targets)):
        target = delete_node.targets[i];

        result = result + compile_expression(target);
        result = result + " = nil";
        if i < len(delete_node.targets) - 1:
            result = result + "; ";

    return result;

def compile_augmentedassignment(node: lua_ast.AugmentedAssignmentNode) -> str:
    result = initialise_string(node);

    parenthesis = node.operator.parenthesis;

    if parenthesis:
        result = result + node.operator.value + "(";
        result = result + compile_expression(node.target);
        result = result + ", ";
        result = result + compile_expression(node.value);
        result = result + ")";
    else:
        result = result + compile_expression(node.target);
        result = result + " " + node.operator.value + " ";
        result = result + compile_expression(node.value);
    
    return result;

def compile_comprehensions(comprehensions_nodes: List[lua_ast.ComprehensionNode]) -> str:
    result = "";
    layers: int = 0;

    for i in range(0, len(comprehensions_nodes)):
        comprehension_node = comprehensions_nodes[i];

        result = result + initialise_string(comprehension_node);

        result = result + "(for k,"
        result = result + compile_expression(comprehension_node.target);
        result = result + " in pairs(";
        result = result + compile_expression(comprehension_node.iterable);
        result = result + ") do\n";

        layers += 1;

        result = result + comprehension_node.scope.get_offset(layers) + "local result = {}\n"

        length = len(comprehension_node.conditions);

        if length > 0:
            result = result + comprehension_node.scope.get_offset(layers) + "if ";

            if length == 1:
                result = result + compile_expression(comprehension_node.conditions[0]);
            else:
                result = result + "(";
                for j in range(0, length):
                    condition = comprehension_node.conditions[j];

                    result = result + "("
                    result = result + compile_expression(condition);
                    result = result + ")"
                    
                    # if not last, then "and";
                    if j < length - 1:
                        result = result + " and ";
                
                result = result + ")";

            result = result + " then\n";

            layers += 1;

        result = result + comprehension_node.scope.get_offset(layers) + "table.insert(result, ";
        result = result + compile_expression(comprehension_node.target);
        result = result + ")\n";

        layers -= 1

        result = result + comprehension_node.scope.get_offset(layers) + "end)\n";

    return result;

def compile_comprehension(comprehension_node: lua_ast.ComprehensionNode) -> str:
    result = initialise_string(comprehension_node);

    result = result + "for k,"
    result = result + compile_expression(comprehension_node.target);
    result = result + " in pairs(";
    result = result + compile_expression(comprehension_node.iterable);
    result = result + ") do\n";
    result = result + comprehension_node.scope.get_offset(1) + "local result = {}"

    if len(comprehension_node.conditions) == 0:
        result = result + comprehension_node.scope.get_offset(1) + "table.insert(result, " + compile_expression(comprehension_node.target) + ")";
    #else:
    for condition in comprehension_node.conditions:
        result = result + comprehension_node.scope.get_offset(1) + "if " + compile_expression(condition) + " then\n";
        
        result = result + comprehension_node.scope.get_offset(2) + "table.insert(result, " + compile_expression(comprehension_node.target) + ")";

        result = result + comprehension_node.scope.get_offset(1) + "end\n";

    result = result + comprehension_node.scope.get_offset() + "end\n";

    return result;

def compile_listcomp(listcomp_node: lua_ast.ListCompNode) -> str:
    result = initialise_string(listcomp_node);

    result = result + compile_comprehensions(listcomp_node.generators);

    return result;

def compile_statement(statement_node: lua_ast.StatementNode) -> str:
    if isinstance(statement_node, lua_ast.FunctionNode):
        return compile_function(statement_node);
    elif isinstance(statement_node, lua_ast.IfNode):
        return compile_if(statement_node)
    elif isinstance(statement_node, lua_ast.ReturnNode):
        return compile_return(statement_node)
    elif isinstance(statement_node, lua_ast.CallNode):
        return compile_call(statement_node)
    elif isinstance(statement_node, lua_ast.AssignmentNode):
        return compile_assignment(statement_node)
    elif isinstance(statement_node, lua_ast.WhileNode):
        return compile_while(statement_node)
    elif isinstance(statement_node, lua_ast.ForNode):
        return compile_for(statement_node)
    elif isinstance(statement_node, lua_ast.DeleteNode):
        return compile_delete(statement_node)
    elif isinstance(statement_node, lua_ast.AugmentedAssignmentNode):
        return compile_augmentedassignment(statement_node)

    raise Exception("Unknown statement node type during Lua AST -> Lua compilation " + str(type(statement_node)));

def compile_expression(expression_node: lua_ast.ExpressionNode) -> str:
    if isinstance(expression_node, lua_ast.NameNode):
        return compile_name(expression_node);
    elif isinstance(expression_node, lua_ast.CompareNode):
        return compile_compare(expression_node);
    elif isinstance(expression_node, lua_ast.ConstantNode):
        return compile_constant(expression_node);
    elif isinstance(expression_node, lua_ast.SubscriptNode):
        return compile_subscript(expression_node);
    elif isinstance(expression_node, lua_ast.BinOpNode):
        return compile_binop(expression_node);
    elif isinstance(expression_node, lua_ast.CallNode):
        return compile_call(expression_node);
    elif isinstance(expression_node, lua_ast.TableNode):
        return compile_table(expression_node);
    elif isinstance(expression_node, lua_ast.YieldNode):
        return compile_yield(expression_node);
    elif isinstance(expression_node, lua_ast.AttributeNode):
        return compile_attribute(expression_node);
    elif isinstance(expression_node, lua_ast.ListCompNode):
        return compile_listcomp(expression_node);
    
    raise Exception("Unknown expression node type during Lua AST -> Lua compilation " + str(type(expression_node)));

def compile_line(node: lua_ast.Node) -> str:
    result = "";

    if issubclass(type(node), lua_ast.StatementNode):
        result = result + compile_statement(node);  # type: ignore
    elif issubclass(type(node), lua_ast.ExpressionNode):
        result = result + compile_expression(node);  # type: ignore
    else:
        raise Exception("Unknown node type during Lua AST -> Lua compilation " + str(type(node)));

    result = node.scope.get_offset() + result;

    if options["toggle_lines"]:
        result = result + "--" + str(node.line_begin)
    
    result = result + "\n";

    return result;

def compile_lines(nodes: List[lua_ast.Node]) -> str:
    result = "";

    for node in nodes:
        result = result + compile_line(node);

    return result;

def compile_module(module_node: py_ast.Module) -> str:
    compiled_module_node = map_module(module_node);

    prefix = "-- Compiled with roblox-py:\n-- https://github.com/codetariat/roblox-py\n\n"
    result = prefix + compile_lines(compiled_module_node.body)

    # Check if last char is \n and remove it if it is
    if result[-1] == "\n":
        result = result[:-1]

    return result;