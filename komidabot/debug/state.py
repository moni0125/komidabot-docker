from logging import Logger
from typing import Any, List, Optional


class ProgramStateTrace:
    def __init__(self):
        self._root = InitialProgramState()  # type: ProgramState
        self._current = self._root  # type: ProgramState

    def state(self, state: 'ProgramState'):
        return WithProgramState(self, state)

    def push(self, state: 'ProgramState'):
        assert state is not None

        state.parent = self._current
        self._current.children.append(state)
        self._current = state

    def pop(self):
        assert self._current.parent is not None

        self._current = self._current.parent

    def prepend(self, parent: 'ProgramStateTrace'):
        # Add current tree as child of prepended tree
        parent._current.children.append(self._root)
        # And update our old root's parent accordingly
        self._root.parent = parent._current
        # Then set the new root to the prepended tree's root
        self._root = parent._root

    def append(self, child: 'ProgramStateTrace'):
        # Add child tree as child to current node
        self._current.children.append(child._root)
        # And set the child's parent accordingly
        child._root.parent = self._current

    def get_state(self) -> 'ProgramState':
        return self._current

    def __repr__(self):
        result = []
        current = self._current
        while current is not None:
            result.insert(0, '- ' + repr(current))
            current = current.parent

        return '\n'.join(['Program state trace:'] + result)


class ProgramState:
    def __init__(self):
        self.parent = None  # type: Optional[ProgramState]
        self.children = []  # type: List[ProgramState]


class InitialProgramState(ProgramState):
    def __repr__(self):
        return 'InitialState'


class SimpleProgramState(ProgramState):
    def __init__(self, name: str, data: Any = None):
        super().__init__()
        self.name = name
        self.data = data

    def __repr__(self):
        return 'State({}, {})'.format(repr(self.name), repr(self.data))


class DebuggableException(Exception):
    def __init__(self, message: str, trace: ProgramStateTrace = None):
        super().__init__(message)
        self._trace = trace

    def get_trace(self) -> ProgramStateTrace:
        return self._trace

    def get_or_set_trace(self, trace: ProgramStateTrace) -> ProgramStateTrace:
        if self._trace is None:
            self._trace = trace
        return self._trace

    def get_state(self) -> ProgramState:
        return self._trace.get_state()

    def print_info(self, logger: Logger):
        logger.error('Error trace: {}'.format(self.get_trace()))
        # Redundant log statement:
        # logger.error('Error last state: {}'.format(self.get_state()))
        logger.exception(self)


class WithProgramState:
    def __init__(self, trace: ProgramStateTrace, state: ProgramState):
        self._trace = trace
        self._state = state

    def __enter__(self):
        self._trace.push(self._state)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            if isinstance(exc_val, DebuggableException):
                trace = exc_val.get_or_set_trace(self._trace)
                if trace is not self._trace:
                    trace.prepend(self._trace)
            else:
                raise DebuggableException('Unspecified error', self._trace) from exc_val
        else:
            self._trace.pop()
