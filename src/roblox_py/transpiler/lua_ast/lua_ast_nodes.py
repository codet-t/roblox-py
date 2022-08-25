from typing import Any, List, Literal

class Node:
    def __init__(self, line_begin: int | None):
        from ..scope import LuaScope
        self.line_begin = line_begin;
        self.scope: LuaScope;

class ExpressionNode(Node):
    def __init__(self, line_begin: int | None):
        super().__init__(line_begin)

class Variable(ExpressionNode):
    def __init__(self, name: str, type: Literal['string', 'number', 'table', 'function', 'nil'] | None, 
                 direct: bool, line_begin: int):
        super().__init__(line_begin)
        self.name = name
        self.type = type
        self.direct = direct
        self.administred = False

class StatementNode(Node):
    def __inift__(self, line_begin: int):
        super().__init__(line_begin)

class FunctionNode(StatementNode):
    def __init__(self, name: str | None, args: List[Any],
                 body: List[Any], decorators: List[str], return_annotation: Any,
                 is_lambda: bool, variables: List[Any], yields: List[Node],
                 line_begin: int):
        self.name = name # None if anonymous
        self.args = args
        self.body = body
        self.decorators = decorators # the @ decorators/options above a function
        self.return_annotation = return_annotation # None if no return statement
        self.is_lambda = is_lambda
        self.variables = variables
        self.yields = yields
        self.line_begin = line_begin

class ModuleNode(Node):
    def __init__(self, body: List[Node]):
        super().__init__(None)
        self.body = body

class ReturnNode(StatementNode):
    def __init__(self, value: ExpressionNode | None, line_begin: int):
        super().__init__(line_begin)
        self.value = value

class AttributeNode(ExpressionNode):
    def __init__(self, attributed_to: ExpressionNode, attribute: str, line_begin: int):
        super().__init__(line_begin)
        self.attributed_to = attributed_to
        self.attribute = attribute

class ConstantNode(ExpressionNode):
    def __init__(self, value: Any, type: Literal["nil","boolean","string","number"], line_begin: int):
        super().__init__(line_begin)
        self.value = str(value)
        self.type = type

class SliceNode(ExpressionNode):
    def __init__(self, subscript: Any, lower: ExpressionNode | None, upper: ExpressionNode | None, 
                step: ExpressionNode | None, line_begin: int):
            super().__init__(line_begin)
            self.subscript = subscript
            self.lower = lower
            self.upper = upper
            self.step = step
class SubscriptNode(ExpressionNode):
    def __init__(self, value: ExpressionNode, slice: Any, line_begin: int):
        super().__init__(line_begin)
        self.value = value
        self.slice = slice

class ArgNode(Node):
    def __init__(self, identifier: str, annotation: ExpressionNode | None,
                 line_begin: int):
        super().__init__(line_begin)
        self.identifier = identifier
        self.annotation = annotation
class AssignmentNode(StatementNode):
    def __init__(self, targets: List[ExpressionNode], value: ExpressionNode, line_begin: int):
        super().__init__(line_begin)
        self.targets = targets
        self.value = value

class CallNode(ExpressionNode):
    def __init__(self, value: ExpressionNode, args: List[ExpressionNode], 
                 attributed_to: Node | None, line_begin: int):
        super().__init__(line_begin)
        self.value = value
        self.args = args
        self.attributed_to = attributed_to # None if not attributed to something

class ElseIfNode(StatementNode):
    def __init__(self, condition: ExpressionNode, body: List[Node],
                elsebody: List[Node], line_begin: int):
        super().__init__(line_begin)
        self.condition = condition
        self.body = body
        self.elsebody = elsebody

class IfNode(StatementNode):
    def __init__(self, condition: ExpressionNode, body: List[Node],
                elsebody: List[Node], elseifbody: List[ElseIfNode], line_begin: int):
        super().__init__(line_begin)
        self.condition = condition
        self.body = body
        self.elsebody = elsebody
        self.elseifbody = elseifbody

class NameNode(ExpressionNode):
    def __init__(self, name: str, line_begin: int):
        super().__init__(line_begin)
        self.name = name

class CompareOperatorNode(ExpressionNode):
    def __init__(self, operator: str, parenthesis: bool):
        super().__init__(None)
        self.operator = operator
        self.parenthesis = parenthesis
        
class CmpOpEqNode(CompareOperatorNode):
    def __init__(self):
        super().__init__('==', False)

class CmpOpNotEqNode(CompareOperatorNode):
    def __init__(self):
        super().__init__('~=', False)

class CmpOpLessNode(CompareOperatorNode):
    def __init__(self):
        super().__init__('<', False)

class CmpOpLessEqNode(CompareOperatorNode):
    def __init__(self):
        super().__init__('<=', False)

class CmpOpGreaterNode(CompareOperatorNode):
    def __init__(self):
        super().__init__('>', False)

class CmpOpGreaterEqNode(CompareOperatorNode):
    def __init__(self):
        super().__init__('>=', False)

class CmpOpIsNode(CompareOperatorNode):
    def __init__(self):
        super().__init__('ropy_is', True)

class CmpOpIsNotNode(CompareOperatorNode):
    def __init__(self):
        super().__init__('not ropy_is', True)

class CmpOpInNode(CompareOperatorNode):
    def __init__(self):
        super().__init__('ropy.operator_in', True)

class CmpOpNotInNode(CompareOperatorNode):
    def __init__(self):
        super().__init__('not ropy.operator_in', True)

class CompareNode(ExpressionNode):
    def __init__(self, left: ExpressionNode, operators: List[CompareOperatorNode], comparators: List[ExpressionNode], line_begin: int):
        super().__init__(line_begin)
        self.left = left
        self.operators = operators
        self.comparators = comparators

class OperatorNode(ExpressionNode):
    def __init__(self, value: str, line_begin: int, parenthesis: bool = False):
        super().__init__(line_begin)
        self.value = value
        self.parenthesis = parenthesis

class AddNode(OperatorNode):
    def __init__(self):
        super().__init__('+', False)

class SubNode(OperatorNode):
    def __init__(self):
        super().__init__('-', False)

class MultNode(OperatorNode):
    def __init__(self):
        super().__init__('*', False)

class DivNode(OperatorNode):
    def __init__(self):
        super().__init__('/', False)

class ModNode(OperatorNode):
    def __init__(self):
        super().__init__('%', False)

class MatrixMultNode(OperatorNode):
    def __init__(self):
        super().__init__('ropy_matrixmult', True)
    
class PowNode(OperatorNode):
    def __init__(self):
        super().__init__('ropy_pow', True)

class LShiftNode(OperatorNode):
    def __init__(self):
        super().__init__('ropy_Lshift', True)

class RShiftNode(OperatorNode):
    def __init__(self):
        super().__init__('ropy_Rshift', True)

class BitAndNode(OperatorNode):
    def __init__(self):
        super().__init__('ropy_bitAnd', True)

class BitOrNode(OperatorNode):
    def __init__(self):
        super().__init__('ropy_bitOr', True)

class BitXorNode(OperatorNode):
    def __init__(self):
        super().__init__('ropy_bitXor', True)

class FloorDivNode(OperatorNode):
    def __init__(self):
        super().__init__('ropy_floordiv', True)

class BinOpNode(ExpressionNode):
    def __init__(self, left: ExpressionNode, right: ExpressionNode, operator: OperatorNode, line_begin: int):
        super().__init__(line_begin)
        self.left = left
        self.right = right
        self.operator = operator

class TableNode(ExpressionNode):
    def __init__(self, keys: List[ExpressionNode], values: List[ExpressionNode],
                type: Literal['list'] | Literal['dict'] | Literal['set'] | Literal['tuple'],
                line_begin: int):
        super().__init__(line_begin)
        self.keys = keys
        self.values = values
        self.type = type;

class WhileNode(StatementNode):
    def __init__(self, condition: ExpressionNode, body: List[Node],
                line_begin: int):
        super().__init__(line_begin)
        self.condition = condition
        self.body = body

class YieldNode(ExpressionNode):
    def __init__(self, value: ExpressionNode | None, line_begin: int):
        super().__init__(line_begin)
        self.value = value

class ForNode(StatementNode):
    def __init__(self, target: ExpressionNode, iterable: ExpressionNode, body: List[Node],
                line_begin: int):
        super().__init__(line_begin)
        self.target = target
        self.iterable = iterable
        self.body = body

class DeleteNode(StatementNode):
    def __init__(self, targets: List[ExpressionNode], line_begin: int):
        super().__init__(line_begin)
        self.targets = targets

class AugmentedAssignmentNode(StatementNode):
    def __init__(self, target: ExpressionNode, operator: OperatorNode, value: ExpressionNode, line_begin: int):
        super().__init__(line_begin)
        self.target = target
        self.operator = operator
        self.value = value

class ComprehensionNode(Node):
    def __init__(self, target: ExpressionNode, iterable: ExpressionNode, conditions: List[ExpressionNode], line_begin: int | None):
        super().__init__(line_begin)
        self.target = target
        self.iterable = iterable
        self.conditions = conditions

class ListCompNode(ExpressionNode):
    def __init__(self, elt: ExpressionNode, generators: List[ComprehensionNode], line_begin: int):
        super().__init__(line_begin)
        self.elt = elt
        self.generators = generators