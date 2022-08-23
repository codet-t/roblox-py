from typing import Any, List, Literal
from typing_extensions import Self

class Node:
    def __init__(self, line_begin: int | None, function_node: Any):
        self.function_node = function_node;
        self.line_begin = line_begin

class StatementNode(Node):
    def __init__(self, line_begin: int, function_node: Any):
        super().__init__(line_begin, function_node);

class FunctionNode(StatementNode):
    def __init__(self, name: str | None, args: List[Any],
                 body: List[Any], decorators: List[str], return_annotation: Any,
                 is_lambda: bool,
                 line_begin: int, function_node: Self | None):
        self.name = name # None if anonymous
        self.args = args
        self.body = body
        self.is_lambda = is_lambda
        self.decorators = decorators # the @ decorators/options above a function
        self.return_annotation = return_annotation # None if no return statement
        self.line_begin = line_begin
        self.function_node = function_node # None if global
    
class ExpressionNode(Node):
    def __init__(self, line_begin: int | None, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
class ModuleNode(Node):
    def __init__(self, body: List[Node]):
        super().__init__(None, None)
        self.body = body

class ReturnNode(StatementNode):
    def __init__(self, value: ExpressionNode | None, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.value = value

class AttributeNode(ExpressionNode):
    def __init__(self, value: ExpressionNode, attribute: str, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.value = value
        self.attribute = attribute

class ConstantNode(ExpressionNode):
    def __init__(self, value: Any, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.value = str(value)

class SliceNode(ExpressionNode):
    def __init__(self, subscript: Any, lower: ExpressionNode | None, upper: ExpressionNode | None, 
                step: ExpressionNode | None, line_begin: int, function_node: FunctionNode | None):
            super().__init__(line_begin, function_node)
            self.subscript = subscript
            self.lower = lower
            self.upper = upper
            self.step = step
class SubscriptNode(ExpressionNode):
    def __init__(self, value: ExpressionNode, slice: Any, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.value = value
        self.slice = slice

class ArgNode(Node):
    def __init__(self, identifier: str, annotation: ConstantNode | None,
                 line_begin: int, function_node: FunctionNode):
        super().__init__(line_begin, function_node)
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
                 attributed_to: Node | None, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.value = value
        self.args = args
        self.attributed_to = attributed_to # None if not attributed to something

class IfNode(StatementNode):
    def __init__(self, condition: ExpressionNode, body: List[Node],
                else_body: List[Node], line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.condition = condition
        self.body = body
        self.else_body = else_body

class NameNode(ExpressionNode):
    def __init__(self, name: str, line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.name = name

class CompareOperatorNode(ExpressionNode):
    def __init__(self, operator: str, parenthesis: bool,
                 function_node: FunctionNode | None):
        super().__init__(None, function_node)
        self.operator = operator
        self.parenthesis = parenthesis
        

class CmpOpEqNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('==', False, function_node)

class CmpOpNotEqNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('~=', False, function_node)

class CmpOpLessNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('<', False, function_node)

class CmpOpLessEqNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('<=', False, function_node)

class CmpOpGreaterNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('>', False, function_node)

class CmpOpGreaterEqNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('>=', False, function_node)

class CmpOpIsNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_is', True, function_node)

class CmpOpIsNotNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('not ropy_is', True, function_node)

class CmpOpInNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('ropy_in', True, function_node)

class CmpOpNotInNode(CompareOperatorNode):
    def __init__(self, function_node: FunctionNode | None):
        super().__init__('not ropy_in', True, function_node)

class CompareNode(ExpressionNode):
    def __init__(self, left: ExpressionNode, operators: List[CompareOperatorNode], comparators: List[ExpressionNode], line_begin: int, function_node: FunctionNode | None):
        super().__init__(line_begin, function_node)
        self.left = left
        self.operators = operators
        self.comparators = comparators

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
