"""Tests focusing on AST operations, especially binary operations analysis."""

import ast
import pytest

from core.security import SecurityError
from core.security.strategy_security import StrategySecurity


def test_get_value_source_with_binary_operations():
    """Test the _get_value_source method with binary operations."""
    
    # Create a binary operation: a + b
    left = ast.Name(id="a", ctx=ast.Load())
    right = ast.Name(id="b", ctx=ast.Load())
    bin_op = ast.BinOp(left=left, right=right, op=ast.Add())
    
    # Test _get_value_source with binary operation
    result = StrategySecurity._get_value_source(bin_op)
    assert "operation:variable:a_variable:b" in result
    
    # Create a more complex binary operation: a + (b * 2)
    left = ast.Name(id="a", ctx=ast.Load())
    right_left = ast.Name(id="b", ctx=ast.Load())
    right_right = ast.Constant(value=2)
    right = ast.BinOp(left=right_left, right=right_right, op=ast.Mult())
    complex_bin_op = ast.BinOp(left=left, right=right, op=ast.Add())
    
    # Test _get_value_source with complex binary operation
    result = StrategySecurity._get_value_source(complex_bin_op)
    assert "operation:variable:a_operation:variable:b_constant:int" in result
    
    # Test with a constant in a binary operation
    left = ast.Constant(value=5)
    right = ast.Name(id="x", ctx=ast.Load())
    const_bin_op = ast.BinOp(left=left, right=right, op=ast.Mult())
    
    result = StrategySecurity._get_value_source(const_bin_op)
    assert "operation:constant:int_variable:x" in result


def test_analyze_ast_with_binary_operations():
    """Test analyze_ast with code containing binary operations."""
    
    # Simple arithmetic operations
    simple_arithmetic = """
def calculate(a, b):
    return a + b * 2
"""
    # This should pass as it's simple arithmetic
    StrategySecurity.analyze_ast(simple_arithmetic)
    
    # More complex operations with variables
    complex_arithmetic = """
def calculate_complex(a, b, c):
    result = a + (b * c) / (a - b)
    return result ** 2
"""
    # This should also pass
    StrategySecurity.analyze_ast(complex_arithmetic)
    
    # Operations with string concatenation
    string_operations = """
def build_string(name, age):
    return "Name: " + name + ", Age: " + str(age)
"""
    # This should pass
    StrategySecurity.analyze_ast(string_operations)
    
    # Operations with list comprehensions
    list_operations = """
def process_list(numbers):
    return [x * 2 for x in numbers if x > 0]
"""
    # This should pass
    StrategySecurity.analyze_ast(list_operations)


def test_get_value_source_with_various_nodes():
    """Test _get_value_source with various AST node types."""
    
    # Create a Call node
    func = ast.Name(id="func", ctx=ast.Load())
    call_node = ast.Call(func=func, args=[], keywords=[])
    
    # Test _get_value_source with Call node
    result = StrategySecurity._get_value_source(call_node)
    assert "function:func" in result
    
    # Test with an unknown node type
    class CustomNode(ast.AST):
        pass
    
    custom_node = CustomNode()
    
    # Test _get_value_source with custom node
    result = StrategySecurity._get_value_source(custom_node)
    assert result == "unknown"


def test_analyze_ast_with_complex_expressions():
    """Test analyze_ast with code containing complex expressions."""
    
    # Code with list comprehensions and lambda expressions
    complex_expressions = """
def process_data(data):
    # List comprehension with lambda
    result = [(lambda x: x * 2)(item) for item in data if item > 0]
    
    # Dictionary comprehension
    result_dict = {k: v for k, v in zip(range(len(result)), result)}
    
    # Generator expression
    gen = (x for x in result if x % 2 == 0)
    
    return list(gen), result_dict
"""
    # This should pass
    StrategySecurity.analyze_ast(complex_expressions)
    
    # Code with complex boolean operations
    boolean_operations = """
def check_conditions(a, b, c, d):
    return (a > 0 and b < 10) or (c == d and not (a == b))
"""
    # This should pass
    StrategySecurity.analyze_ast(boolean_operations)
    
    # Code with nested function calls
    nested_calls = """
def nested_function_calls(x):
    return abs(round(float(str(x))))
"""
    # This should pass
    StrategySecurity.analyze_ast(nested_calls)


def test_analyze_ast_with_potentially_dangerous_patterns():
    """Test analyze_ast with code that contains potentially dangerous patterns."""
    
    # Code with exec-like pattern in a string
    exec_pattern = """
def dangerous_function(cmd):
    command = f"result = {cmd}"
    # This would be caught by other security checks
    return command
"""
    # This should pass the AST check but would be caught by Bandit
    StrategySecurity.analyze_ast(exec_pattern)
    
    # Code with format string that looks like command injection
    format_string = """
def format_message(user_input):
    return f"Hello, {user_input}!"
"""
    # This should pass
    StrategySecurity.analyze_ast(format_string)
    
    # Code with string operations that might be used to obfuscate dangerous code
    obfuscation_pattern = """
def obfuscated():
    a = "ev"
    b = "al"
    c = a + b
    return c  # Returns "eval" string but doesn't call it
"""
    # This should pass the AST check but might be caught by data flow analysis
    StrategySecurity.analyze_ast(obfuscation_pattern)
    

def test_get_call_descriptor_with_complex_calls():
    """Test _get_call_descriptor with complex call patterns."""
    
    # Test with a nested method call: obj.inner.method()
    inner_obj = ast.Name(id="obj", ctx=ast.Load())
    inner_attr = ast.Attribute(value=inner_obj, attr="inner", ctx=ast.Load())
    method_attr = ast.Attribute(value=inner_attr, attr="method", ctx=ast.Load())
    call_node = ast.Call(func=method_attr, args=[], keywords=[])
    
    result = StrategySecurity._get_call_descriptor(call_node)
    assert "method:obj.inner.method" in result
    
    # Test with a subscript call: obj["key"].method()
    obj = ast.Name(id="obj", ctx=ast.Load())
    key = ast.Constant(value="key")
    subscript = ast.Subscript(value=obj, slice=key, ctx=ast.Load())
    method_attr = ast.Attribute(value=subscript, attr="method", ctx=ast.Load())
    call_node = ast.Call(func=method_attr, args=[], keywords=[])
    
    # This would return "unknown" because _get_attr_source doesn't handle Subscript nodes
    result = StrategySecurity._get_call_descriptor(call_node)
    assert "method:" in result
    
    # Test with a non-Name, non-Attribute func
    call_node = ast.Call(func=ast.Constant(value=None), args=[], keywords=[])
    result = StrategySecurity._get_call_descriptor(call_node)
    assert result == "unknown_call" 