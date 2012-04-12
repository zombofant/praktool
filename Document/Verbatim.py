# encoding=utf-8
r"""
Implement a simple template language, which allows for *arbitary* python
code to be placed in any plain text.

Template syntax
---------------

On startup, the template parser assumes it is parsing a raw plaintext
document of whose syntax it has no idea. So the template syntax is kept
in a way which allows for maximum compatibility (just like string
literals in most languages).

To start a python source section, you must escape it by ``<? … ?>``, as
you might be used to do in other languages. For example, the following
would be a valid template and render a TeX document::

    \documentclass[10pt]{scrartcl}

    \begin{document}
        <? " ".join(["Hello", "World"]) ?>
    \end{document}

It will, of course, just show ``Hello World`` when being rendered. If
you actually need a literal ``<?`` in your target document, you can
either just output in in python or escape it::

    % TeX source goes here
    <? "<?" ?>
    % does the same:
    \<?

To allow for maximum compatibilty, backslashes (``\\``) are ignored and
printed just as taken if they are not followed by a ``<?``. If you need
a literal ``\\<?``, you can either escape it with one more backslash
or print it from python.

The parser will just do the same as the repl shell does. Every
non-catched return value will be collected, converted to its unicode
representation and added to the output document, without any spacing
between the values. If you need newlines or spaces, just put them into
the source literally::

    <?
        for x in range(10):
            "\n"
    ?>

This will give you 10 newlines. You can change the default behaviour of
creating the string representation in the :class:`Template` class.

Note that for now, the python code state is not aware of python
string literals or similar. So you **cannot** do the following::

    <? "?>" ?>

The parser will assume the python section ends at ``"?>``, which will
obviously SyntaxError.
"""
from __future__ import division, unicode_literals, print_function
from our_future import *

import re
import abc

import codeop

class SwitchState(Exception):
    """
    Used by the parser states internally to signal the end of a
    context and that a switch to another context has to take place.

    If *newState* is set, the current state will be replaced with
    *newState*, otherwise it is popped off the state stack and
    tokenization continues with the previous state.
    """

    def __init__(self, newState=None):
        self.newState = newState

    def __unicode__(self):
        return super(SwitchState, self).__unicode__() + "; This is actually an internal parser exception and should *never* be displayed. This is a bug."

class ParserState(object):
    """
    Baseclass for parser state.

    *charIterable* will throw EOFError when no more data is available
    instead of StopIteration.
    """
    
    __metaclass__ = abc.ABCMeta
    inlinePrefix = re.compile(r"(?<!\\)<\?")
    
    def __init__(self, charIterable, **kwargs):
        self.chars = charIterable

    @abc.abstractmethod
    def next(self):
        pass

class TemplateSection(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __hash__(self):
        pass

    @abc.abstractmethod
    def __eq__(self):
        pass

    @abc.abstractmethod
    def __ne__(self):
        pass

class SectionLiteral(TemplateSection): 
    def __init__(self, s, **kwargs):
        self._s = s

    def eval(self, globals, locals):
        return self._s

    def __hash__(self):
        return hash((SectionLiteral, self._code))

    def __eq__(self, other):
        if not isinstance(other, TemplateSection):
            return NotImplemented
        elif not isinstance(other, SectionLiteral):
            return False
        return (self._s == other._s)

    def __ne__(self, other):
        if not isinstance(other, TemplateSection):
            return NotImplemented
        else:
            return not self.__eq__(other)

    def __repr__(self):
        return "SectionLiteral({0!r})".format(self._s)

    def __unicode__(self):
        return self._s

class SectionPython(TemplateSection):
    compiler = codeop.CommandCompiler()
    indentMatch = re.compile("^ *")
    # strips everything before the first non-empty line
    lstripMatch = re.compile("^\s*\n")
    rstripMatch = re.compile("\n\s*$")

    @classmethod
    def normalizeIndent(cls, source):
        if not "\n" in source:
            stripped = source.strip()
        else:
            # better stripping for multiline code
            stripped = source
            m = cls.lstripMatch.search(stripped)
            if m:
                stripped = stripped[len(m.group(0)):]
            m = cls.rstripMatch.search(stripped)
            if m:
                stripped = stripped[:-len(m.group(0))]
        lines = stripped.split("\n")
        commonIndent = None
        indentMatch = cls.indentMatch
        for line in lines:
            m = indentMatch.search(line)
            if m:
                indent = m.group(0)
                if commonIndent is not None:
                    if len(indent) < commonIndent:
                        commonIndent = len(indent)
                else:
                    commonIndent = len(indent)
                if commonIndent == 0:
                    # we will never be below 0, early out
                    break
        if commonIndent > 0:
            return ("\n".join((line[commonIndent:] for line in lines))) + "\n"
        else:
            return stripped + "\n"
    
    def __init__(self, code, compiler=compiler, fileName="<unknown>", **kwargs):
        self._source = self.normalizeIndent(code)
        self._code = compiler(self._source, fileName)
        if self._code is None:
            raise SyntaxError("Incomplete statement: \n{0}".format(self._source))
        
    def eval(self, globals, locals):
        exec self._code in globals, locals

    def __hash__(self):
        return hash((SectionPython, self._code))

    def __eq__(self, other):
        if not isinstance(other, TemplateSection):
            return NotImplemented
        elif not isinstance(other, SectionPython):
            return False
        return (self._source == other._source)

    def __ne__(self, other):
        if not isinstance(other, TemplateSection):
            return NotImplemented
        else:
            return not self.__eq__(other)

    def __repr__(self):
        return "SectionPython({0!r})".format(self._source)

    def __unicode__(self):
        return "<?{0}?>".format(self._source)

class DelimiterSwitchState(ParserState):
    def __init__(self, charIterable, delimiter, nextStateClass,
            sectionClass, **kwargs):
        super(DelimiterSwitchState, self).__init__(charIterable)
        self.delimiter = delimiter
        self.nextStateClass = nextStateClass
        self.sectionClass = sectionClass
        self.nextException = None

    def yieldAndRaise(self, buffer, exc):
        if len(buffer) > 0:
            self.nextException = exc
            return self.sectionClass(buffer)
        else:
            raise exc

    def next(self):
        if self.nextException is not None:
            nextException = self.nextException
            self.nextException = None
            raise nextException
        backslashes = 0
        delimiter = self.delimiter
        delimiterIndex = 0
        chars = self.chars
        buffer = ""
        try:
            while True:
                char = next(chars)
                if char == delimiter[delimiterIndex]:
                    delimiterIndex += 1
                    if delimiterIndex == len(delimiter):
                        if backslashes == 0:
                            return self.yieldAndRaise(buffer, SwitchState(self.nextStateClass(chars)))
                        else:
                            buffer += ("\\"*(backslashes-1)) + self.delimiter
                        delimiterIndex = 0
                        backslashes = 0
                elif char == "\\":
                    if delimiterIndex > 0:
                        buffer += ("\\"*backslashes) + delimiter[:delimiterIndex]
                        delimiterIndex = 0
                        backslashes = 0
                    else:
                        backslashes += 1
                else:
                    if delimiterIndex or backslashes:
                        buffer += ("\\"*backslashes) + delimiter[:delimiterIndex]
                        delimiterIndex = 0
                        backslashes = 0
                    buffer += char
        except (EOFError, StopIteration) as err:
            buffer += (r"\\"*backslashes) + delimiter[:delimiterIndex]
            return self.yieldAndRaise(buffer, err)

class StateRaw(DelimiterSwitchState):
    def __init__(self, charIterable, **kwargs):
        super(StateRaw, self).__init__(charIterable, "<?", StatePython,
            SectionLiteral)

class StatePython(DelimiterSwitchState):
    def __init__(self, charIterable, **kwargs):
        super(StatePython, self).__init__(charIterable, "?>", StateRaw,
            SectionPython)

    def next(self):
        try:
            return super(StatePython, self).next()
        except EOFError:
            raise ValueError("Premature end of stream.")

class Parser(object):
    @staticmethod
    def lineToChars(lineIterable):
        """
        Takes an iterable which yields string lines, including the final
        newline and yields a character for each character in each line
        (again, including the newline).

        Unconditionally raises an EOFError at the end of lineIterable.
        """
        for line in lineIterable:
            for char in line:
                yield char
        raise EOFError
    
    def __init__(self, lineIterable, **kwargs):
        super(Parser, self).__init__(**kwargs)
        self.chars = self.lineToChars(lineIterable)
        self.states = [StateRaw(self.chars)]

    def __iter__(self):
        return self

    def next(self):
        while True:
            try:
                state = self.states[-1]
            except IndexError:
                raise StopIteration
            try:
                return next(state)
            except SwitchState as err:
                if err.newState is not None:
                    self.states[-1] = err.newState
                else:
                    self.states.pop()
            except EOFError:
                raise StopIteration

class Template(object):
    def __init__(self, filelike, **kwargs):
        super(Template, self).__init__(**kwargs)
        sections = list(Parser(filelike))
