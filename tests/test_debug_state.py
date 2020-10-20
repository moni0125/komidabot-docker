import unittest

from komidabot.debug.state import DebuggableException, ProgramStateTrace, SimpleProgramState


class TestConstants(unittest.TestCase):
    """
    Tests to see if komidabot.debug.state works properly.
    """

    def test_no_raise(self):
        # Checks that ProgramStateTrace.state does not raise on its self.
        debug_state = ProgramStateTrace()

        with debug_state.state(SimpleProgramState('Test state')):
            pass

    def test_simple_raise(self):
        # Checks that ProgramStateTrace.state catches exceptions and rethrows them as DebuggableException.
        debug_state = ProgramStateTrace()

        with self.assertRaises(DebuggableException) as caught:
            with debug_state.state(SimpleProgramState('Test state 1')):
                raise Exception('Test exception')

        expected = '\n'.join([
            "Program state trace:",
            "- InitialState",
            "- State('Test state 1', None)",
        ])
        ex: DebuggableException = caught.exception

        self.assertEqual(expected, repr(ex.get_trace()))

    def test_simple_nested(self):
        # Checks that simple nested states are properly returned
        debug_state = ProgramStateTrace()

        with self.assertRaises(DebuggableException) as caught:
            with debug_state.state(SimpleProgramState('Test state 1')):
                with debug_state.state(SimpleProgramState('Test state 2')):
                    raise Exception('Test exception')

        expected = '\n'.join([
            "Program state trace:",
            "- InitialState",
            "- State('Test state 1', None)",
            "- State('Test state 2', None)",
        ])
        ex: DebuggableException = caught.exception

        self.assertEqual(expected, repr(ex.get_trace()))

    def test_simple_branched(self):
        # Checks that only the branch where the exception occurred is returned
        debug_state = ProgramStateTrace()

        with self.assertRaises(DebuggableException) as caught:
            with debug_state.state(SimpleProgramState('Test state 1')):
                with debug_state.state(SimpleProgramState('Test state 1a')):
                    pass
                with debug_state.state(SimpleProgramState('Test state 1b')):
                    pass
                with debug_state.state(SimpleProgramState('Test state 1c')):
                    pass
            with debug_state.state(SimpleProgramState('Test state 2')):
                with debug_state.state(SimpleProgramState('Test state 2a')):
                    pass
                with debug_state.state(SimpleProgramState('Test state 2b')):
                    raise Exception('Test exception')
                with debug_state.state(SimpleProgramState('Test state 2c')):
                    pass
            with debug_state.state(SimpleProgramState('Test state 3')):
                with debug_state.state(SimpleProgramState('Test state 3a')):
                    pass
                with debug_state.state(SimpleProgramState('Test state 3b')):
                    pass
                with debug_state.state(SimpleProgramState('Test state 3c')):
                    pass

        expected = '\n'.join([
            "Program state trace:",
            "- InitialState",
            "- State('Test state 2', None)",
            "- State('Test state 2b', None)",
        ])
        ex: DebuggableException = caught.exception

        self.assertEqual(expected, repr(ex.get_trace()))

    def test_multi_nested(self):
        # Checks that nested states from different traces are properly returned
        debug_state1 = ProgramStateTrace()

        with self.assertRaises(DebuggableException) as caught:
            with debug_state1.state(SimpleProgramState('Test state 1')):
                debug_state2 = ProgramStateTrace()

                with debug_state2.state(SimpleProgramState('Test state 2')):
                    raise Exception('Test exception')

        expected = '\n'.join([
            "Program state trace:",
            "- InitialState",
            "- State('Test state 1', None)",
            "- InitialState",
            "- State('Test state 2', None)",
        ])
        ex: DebuggableException = caught.exception

        self.assertEqual(expected, repr(ex.get_trace()))

    def test_multi_branched(self):
        # Checks that only the branch where the exception occurred is returned, even if we have different traces
        debug_state1 = ProgramStateTrace()

        with self.assertRaises(DebuggableException) as caught:
            with debug_state1.state(SimpleProgramState('Test state 1')):
                debug_state2 = ProgramStateTrace()
                with debug_state2.state(SimpleProgramState('Test state 1a')):
                    pass
                with debug_state2.state(SimpleProgramState('Test state 1b')):
                    pass
                with debug_state2.state(SimpleProgramState('Test state 1c')):
                    pass
            with debug_state1.state(SimpleProgramState('Test state 2')):
                debug_state2 = ProgramStateTrace()
                with debug_state2.state(SimpleProgramState('Test state 2a')):
                    pass
                with debug_state2.state(SimpleProgramState('Test state 2b')):
                    raise Exception('Test exception')
                with debug_state2.state(SimpleProgramState('Test state 2c')):
                    pass
            with debug_state1.state(SimpleProgramState('Test state 3')):
                debug_state2 = ProgramStateTrace()
                with debug_state2.state(SimpleProgramState('Test state 3a')):
                    pass
                with debug_state2.state(SimpleProgramState('Test state 3b')):
                    pass
                with debug_state2.state(SimpleProgramState('Test state 3c')):
                    pass

        expected = '\n'.join([
            "Program state trace:",
            "- InitialState",
            "- State('Test state 2', None)",
            "- InitialState",
            "- State('Test state 2b', None)",
        ])
        ex: DebuggableException = caught.exception

        self.assertEqual(expected, repr(ex.get_trace()))
