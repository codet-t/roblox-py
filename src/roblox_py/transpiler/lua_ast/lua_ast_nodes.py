from typing import List, Literal

class FunctionNode:  # type: ignore
    pass;

class Node:
    def __init__(self, line_begin: int | None, function_node: FunctionNode | None):
        function_node = function_node;
        line_begin = line_begin

class StatementNode(Node):
    def __init__(self, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node);

class ModuleNode(Node):
    def __init__(self, body: List[StatementNode]):
        super().__init__(None, None)
        self.body = body
    
class ExpressionNode(Node):
    def __init__(self, line_begin: int | None, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)

class ReturnNode(StatementNode):
    def __init__(self, value: str | None, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.value = value

class AttributeNode(ExpressionNode):
    def __init__(self, value: ExpressionNode, attribute: str, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.value = value
        self.attribute = attribute

class ArgNode(Node):
    def __init__(self, identifier: str, annotation: AttributeNode | None,
                 line_begin: int):
        super().__init__(line_begin, None)
        self.identifier = identifier
        self.annotation = annotation

class AssignmentNode(StatementNode):
    def __init__(self, targets: List[ExpressionNode], value: ExpressionNode, line_begin: int, 
                 function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.targets = targets
        self.value = value

class Variable(ExpressionNode):
    def __init__(self, name: str, type: Literal['string', 'number' 'table'] | None, 
        line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.name = name
        self.type = type # None
        self.function = function # function it belongs to (None = global)

class CallNode(ExpressionNode):
    def __init__(self, value: ExpressionNode, args: List[ExpressionNode], 
                 attributed_to: List[Node] | None, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.value = value
        self.args = args

class IfNode(StatementNode):
    def __init__(self, condition: ExpressionNode, body: List[StatementNode],
                else_body: List[StatementNode], line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.condition = condition
        self.body = body
        self.else_body = else_body

class NameNode(ExpressionNode):
    def __init__(self, name: str, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.name = name

class CompareOperatorNode(ExpressionNode):
    def __init__(self, operator: str, 
                 function_node: FunctionNode | None):
        super().__init__(None, function_node)
        self.operator = operator

class CmpOpEqNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('==', function_node)

class CmpOpNotEqNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('~=', function_node)

class CmpOpLessNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('<', function_node)

class CmpOpLessEqNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('<=', function_node)

class CmpOpGreaterNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('>', function_node)

class CmpOpGreaterEqNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('>=', function_node)

class CmpOpIsNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_is', function_node)

class CmpOpIsNotNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('not ropy_is', function_node)

class CmpOpInNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_in', function_node)

class CmpOpNotInNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('not ropy_in', function_node)

class CompareNode(ExpressionNode):
    def __init__(self, left: NameNode, operators: List[CompareOperatorNode], comparators: List[ExpressionNode], line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.left = left
        self.operators = operators
        self.comparators = comparators

class ConstantNode(ExpressionNode):
    def __init__(self, value: str, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.value = value

class OperatorNode(ExpressionNode):
    def __init__(self, operator: str, line_begin: int, function_node: FunctionNode | None, parenthesis: bool = False):
        super().__init__(line_begin, function_node)
        self.operator = operator
        self.parenthesis = parenthesis

class AddNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('+', False, function_node)

class SubNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('-', False, function_node)

class MultNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('*', False, function_node)

class DivNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('/', False, function_node)

class ModNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('%', False, function_node)

class MatrixMultNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_matrixmult', True, function_node)
    
class PowNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_pow', True, function_node)

class LShiftNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_Lshift', True, function_node)

class RShiftNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_Rshift', True, function_node)

class BitAndNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_bitAnd', True, function_node)

class BitOrNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_bitOr', True, function_node)

class BitXorNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_bitXor', True, function_node)

class FloorDivNode(OperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_floordiv', True, function_node)

class BinOpNode(ExpressionNode):
    def __init__(self, left: ExpressionNode, right: ExpressionNode, operator: OperatorNode, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.left = left
        self.right = right
        self.operator = operator

class FunctionNode(StatementNode):
    def __init__(self, name: str | None, args: List[ArgNode], 
                 body: List[StatementNode], decorators: List[str], return_annotation: str | None,
                 line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.name = name # None if anonymous
        self.args = args
        self.body = body
        self.decorators = decorators # the @ decorators/options above a function
        self.return_annotation = return_annotation # None if no return statement