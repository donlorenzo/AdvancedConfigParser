# -*- coding: utf-8 -*-

# Copyright (c) 2010, 2014 Lorenz Quack
# This code is released under the MIT License:
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

u"""
AdvancedConfigParser

parse config files written in a .ini-file like style.
In addition to ini files this module has the following advanced features:
 * arbitrarily nested subsections
 * various (nested) types including int, float, str, list, dict
 * various calculations in values
 * refer to other keys in values

Example:

global_var = True
[Section_1]
pi = 3.141
[[Sub_Sec_1]]
tau = 2 * pi
[whatever]
foo = [Section_1.pi, Section_1.Sub_Section_1.tau, global_var]
bar = max(foo)
baz = foo if Section_1.pi < 2**2 < Section_1.Sub_Sec_1.tau/2 or True else bar

Configuration can be loaded from strings (parse_string()),
files (parse_file()) or file-like objects (parse_stream()).
Access to the sections and options is done by attribute access:
>>> config = AdvancedConfigParser.parse_string("filename")
>>> print(config.global_var)
>>> print(config.Section_1.pi + config.whatever.bar)
"""

try:
    import __builtin__ as builtins
except ImportError:
    import builtins

import io
import re
import ast
import operator

from ast_to_src import ast_to_src

def parse_file(filename):
    with open(filename) as f:
        return parse_stream(f)

def parse_string(s):
    return parse_stream(io.StringIO(s))

def parse_stream(stream):
    """
    parse the stream into a hirarchical tree of (sub-)sections and options.
    return the root/global section.
    """
    root = current_section = Section()
    current_section._acp_name = "<global>"
    current_nesting_level = 0
    line = 0
    while True:
        buf = ""
        tmp = stream.readline()
        line += 1
        if tmp == "":
            break
        buf += tmp
        stripped_buf = buf.strip()

        # preserve empty lines
        if not stripped_buf:
            current_section._acp_add_empty_line()
        # ignore comments
        elif stripped_buf.startswith("#"):
            current_section._acp_add_comment(stripped_buf)

        # handle section header
        elif stripped_buf.startswith("["):
            result = re.match(r"(\[+)([^\d\W]\w*)(\]+)", stripped_buf)
            if result is None:
                msg = "malformed section header in line {line}:\n{tmp}"
                raise SyntaxError(msg.format(**locals()))
            if len(result.group(1)) != len(result.group(3)):
                msg = "section braket mismatch in line {line}:\n{tmp}"
                raise SyntaxError(msg.format(**locals()))
            level = min(len(result.group(1)), len(result.group(3)))
            if level > current_nesting_level + 1:
                msg = "wrong section nesting in line {line}"
                raise SyntaxError(msg.format(**locals()))
            while current_nesting_level >= level:
                current_section = current_section._acp_parent
                current_nesting_level -= 1
            section_name = ast.parse(result.group(2)).body[0].value.id
            if section_name in list(current_section._acp_section_names()):
                msg = 'duplicate section "{section_name}".'.format(**locals())
                raise SyntaxError(msg)
            new_section = Section()
            new_section._acp_name = section_name
            current_section._acp_add_child(new_section)
            current_section = new_section
            current_nesting_level += 1

        # handle options
        else:
            node = None
            while node is None and tmp != "":
                try:
                    node = ast.parse(stripped_buf)
                except SyntaxError:
                    tmp = stream.readline()
                    buf += tmp
                    stripped_buf = buf.strip()
            node = node.body[0]
            assert isinstance(node, ast.Assign)
            option_name = node.targets[0].id
            if option_name in list(current_section._acp_option_names()):
                msg = ('duplicate option "{option_name}" in '
                       'section "{current_section._acp_name}".')
                raise SyntaxError(msg.format(**locals()))
            new_option = Option()
            new_option._acp_name = option_name
            new_option._acp_value = node.value
            current_section._acp_add_child(new_option)
    return root

class Section(object):
    """
    Section objects allow access to their sub-sections and options via
    attribute access and subscript.
    new sections and options may be added via "_acp_add_child()".
    """
    def __init__(self):
        self.__dict__["_acp_name"] = ""
        self.__dict__["_acp_parent"] = None
        self.__dict__["_acp_order"] = []
        self.__dict__["_acp_nesting_level"] = 0

    def __str__(self):
        return '<Section "{self._acp_name}">'.format(**locals())
    __repr__ = __str__

    def __setattr__(self, attr, val):
        obj = object.__getattribute__(self, attr)
        if isinstance(obj, Option):
            obj._acp_value = val
        else:
            super(Section, self).__setattr__(attr, val)

    def __getattribute__(self, attr, raw=False):
        obj = super(Section, self).__getattribute__(attr)
        if isinstance(obj, Option) and not raw:
            return obj._acp_value
        else:
            return obj

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError as e:
            raise KeyError(str(e))

    def _acp_add_child(self, child):
        child._acp_nesting_level = self._acp_nesting_level + 1
        if child._acp_parent is None:
            child._acp_parent = self
        if child._acp_name in self.__dict__:
            msg = "duplicate object: {child_name}"
            raise SyntaxError(msg.format(child_name=child._acp_name))
        self.__dict__[child._acp_name] = child
        self.__dict__["_acp_order"].append(child._acp_name)

    def _acp_add_empty_line(self):
        self.__dict__["_acp_order"].append("\n")

    def _acp_add_comment(self, comment):
        self.__dict__["_acp_order"].append(comment)

    def _acp_sections(self):
        for section in (section for section in self.__dict__.values()
                        if isinstance(section, Section)):
            yield section
    def _acp_section_names(self):
        for section_name in (sn for (sn, s) in self.__dict__.items()
                             if isinstance(s, Section)):
            yield section_name

    def _acp_options(self):
        for option in (option for option in self.__dict__.values()
                       if isinstance(option, Option)):
            yield option
    def _acp_option_names(self):
        for option_name in (o_name for o_name, option in self.__dict__.items()
                            if isinstance(option, Option)):
            yield option_name

    def _acp_children(self):
        for child in (child for child in self.__dict__.values()
                      if isinstance(child, (Section, Option))):
            yield child

    def dump(self):
        return self.pretty_print(do_indent=False)

    def pretty_print(self, indent=0, do_indent=True):
        if self._acp_name != "<global>":
            template = "{indentation}{left}{section_name}{right}\n"
            s = template.format(indentation=" " * indent,
                                left="[" * self._acp_nesting_level,
                                right="]" * self._acp_nesting_level,
                                section_name=self._acp_name)
            if do_indent:
                indent += 1
        else:
            s = ""
        for child_name in self._acp_order:
            if child_name == "\n":
                s += "\n"
            elif child_name.strip().startswith("#"):
                s += "{indent}{comment}\n".format(indent=" " * indent,
                                                  comment=child_name)
            else:
                child = getattr(self, child_name)
                if isinstance(child, Section):
                    s += child.pretty_print(indent)
                else:
                    child_raw = self._acp_get_raw_option(child_name)
                    template = "{indentation}{option_name} = {option_raw}\n"
                    s += template.format(indentation=" " * indent,
                                         option_name=child_name,
                                         option_raw=child_raw)
        return s

    def _acp_get_raw_option(self, option_name):
        return self.__getattribute__(option_name, True)._acp_raw_value

class LazyEval(object):
    """
    evaluates the ast nodes lazy when used as a descriptor.
    when we find that all involved ast-nodes are static we cache the result.
    """
    def __init__(self):
        self.cache = {}

    def __get__(self, instance, owner):
        # see if we already cached the result from a previous evaluation
        if instance in self.cache:
            return self.cache[instance]
        # dynamically evaluate the ast-nodes
        val, has_refs = self._acp_eval(instance._acp_parent,
                                       instance._acp_ast_node)
        # if the ast-nodes have no external references cache the result
        if not has_refs:
            self.cache[instance] = val
        return val

    def __set__(self, instance, value):
        # if value is a ast-node invalidate the cache
        if isinstance(value, ast.AST):
            instance._acp_ast_node = value
            try:
                del self.cache[instance]
            except KeyError:
                pass
        # else it is a static value which can be put directly into the cache
        else:
            self.cache[instance] = value

    def _acp_eval(self, parent, node):
        """
        dynamically and recursively evaluate the ast-nodes.
        returns a 2-tuple. first is the actual value, second a bool indicating
        if this ast-node has external dependencies and should not be cached.
        """
        # first try simple conversion of literals
        try:
            return ast.literal_eval(node), False
        except (SyntaxError, ValueError):
            pass
        # handle external references
        if isinstance(node, (ast.Name, ast.Attribute)):
            ref = ""
            while isinstance(node, ast.Attribute):
                ref = "." + node.attr + ref
                node = node.value
            ref = node.id + ref
            return self._acp_resolve_reference(ref, parent), True
        # handle lists, tuples and dicts
        elif isinstance(node, (ast.List, ast.Tuple, ast.Dict)):
            vals = []
            has_refs = False
            for child_node in ast.iter_child_nodes(node):
                tmp = self._acp_eval(parent, child_node)
                if not tmp:
                    continue
                vals.append(tmp[0])
                has_refs = tmp[1]
            if isinstance(node, ast.List):
                return list(vals), has_refs
            elif isinstance(node, ast.Tuple):
                return tuple(vals), has_refs
            return vals, has_refs
        # handle the following math operators +, -, *, /, //, %, **, |, &, ^
        elif isinstance(node, ast.BinOp):
            lhs, lhs_has_refs = self._acp_eval(parent, node.left)
            rhs, rhs_has_refs = self._acp_eval(parent, node.right)
            ops = {ast.Add: operator.add, ast.Sub: operator.sub,
                   ast.Mult: operator.mul, ast.Div: operator.truediv,
                   ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
                   ast.Pow: operator.pow, ast.LShift: operator.lshift,
                   ast.RShift: operator.rshift, ast.BitOr: operator.or_,
                   ast.BitXor: operator.xor, ast.BitAnd: operator.and_,}
            if node.op.__class__ in ops:
                return (ops[node.op.__class__](lhs, rhs),
                        lhs_has_refs | rhs_has_refs)
            else:
                msg = 'op "{op_name}" not supported yet'
                raise SyntaxError(msg.format(op_name=str(node.op.__class__)))
        # handle calls to some selected builtin functions
        elif isinstance(node, ast.Call):
            if node.func.id in ("abs", "all", "any", "bin", "bool", "chr",
                                "complex", "dict", "divmod", "enumerate",
                                "float", "hex", "int", "len", "list", "max",
                                "min", "oct", "ord", "pow", "range", "reversed",
                                "round", "set", "sorted", "str", "sum", "tuple",
                                "type", "unichr", "zip", ):
                has_refs = False
                args = []
                for arg_node in node.args:
                    arg, temp_has_refs = self._acp_eval(parent, arg_node)
                    args.append(arg)
                    has_refs |= temp_has_refs
                kwargs = {}
                for keyword_node in node.keywords:
                    kwargs[keyword_node.arg], temp_has_refs = self._acp_eval(parent, keyword_node.value)
                    has_refs |= temp_has_refs
                return (builtins.__dict__[node.func.id](*args, **kwargs),
                        has_refs)
        # handle ternary if operator
        elif isinstance(node, ast.IfExp):
            test, test_has_refs = self._acp_eval(parent, node.test)
            if test:
                result, has_refs = self._acp_eval(parent, node.body)
            else:
                result, has_refs = self._acp_eval(parent, node.orelse)
            return result, has_refs | test_has_refs
        # handle compares
        elif isinstance(node, ast.Compare):
            astOp2FuncOp = {ast.Eq: operator.eq, ast.NotEq: operator.ne,
                            ast.Lt: operator.lt, ast.LtE: operator.le,
                            ast.Gt: operator.gt, ast.GtE: operator.ge,
                            ast.Is: operator.is_, ast.IsNot: operator.is_not,
                            # don't use contains because arguments are reversed
                            ast.In: lambda a, b: a in b,
                            ast.NotIn: lambda a, b: a not in b}
            left, left_has_refs = self._acp_eval(parent, node.left)
            has_refs = left_has_refs
            for ast_op, ast_right in zip(node.ops, node.comparators):
                right, right_has_refs = self._acp_eval(parent, ast_right)
                has_refs |= right_has_refs
                op = astOp2FuncOp[ast_op.__class__]
                if op(left, right):
                    left = right
                else:
                    return False, has_refs
            return True, has_refs
        # handle boolean operators
        elif isinstance(node, ast.BoolOp):
            has_refs = False
            if node.op.__class__ == ast.And:
                for value in node.values:
                    v, value_has_refs = self._acp_eval(parent, value)
                    has_refs |= value_has_refs
                    if not v:
                        return False, has_refs
                return True, has_refs
            elif node.op.__class__ == ast.Or:
                for value in node.values:
                    v, value_has_refs = self._acp_eval(parent, value)
                    has_refs |= value_has_refs
                    if v:
                        return True, has_refs
                return False, has_refs
            raise RuntimeError("unreachable")
        # not sure what this is about...
        elif isinstance(node, ast.Load):
            pass
        else:
            raise RuntimeError("unhandled node: " + str(node))

    @classmethod
    def _acp_resolve_reference(cls, ref, parent):
        """
        resolves external references by walking up the tree
        until we find a complete match
        """
        attrs = ref.split(".")
        while parent is not None:
            try:
                obj = parent
                for attr in attrs:
                    obj = getattr(obj, attr)
                return obj
            except (KeyError, AttributeError):
                parent = parent._acp_parent
        raise AttributeError(ref)


class Option(object):
    def __init__(self):
        self._acp_name = ""
        self._acp_parent = None
        self._acp_has_refs = True
        self._acp_nesting_level = 0
        self._acp_ast_node = None

    def _acp_get_raw_value(self):
        return ast_to_src(self._acp_ast_node)

    _acp_value = LazyEval()
    _acp_raw_value = property(_acp_get_raw_value)

    def __str__(self):
        return '<Option {self._acp_name}>'.format(**locals())
    __repr__ = __str__

