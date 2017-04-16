import unittest
import labels2tables.uniquebool as uniquebool
import copy

class TestUniquebool(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_equality(self):
        self.assertNotEqual(uniquebool.TRUE, True)
        self.assertNotEqual(uniquebool.TRUE, 1)
        self.assertNotEqual(uniquebool.FALSE, False)
        self.assertNotEqual(uniquebool.FALSE, 0)
        self.assertNotEqual(uniquebool.TRUE, uniquebool.FALSE)
        self.assertEqual(uniquebool.TRUE, copy.deepcopy(uniquebool.TRUE))
        self.assertEqual(uniquebool.FALSE, copy.deepcopy(uniquebool.FALSE))
    
    def test_print(self):
        self.assertEqual(str(uniquebool.TRUE), "TRUE")
        self.assertEqual(str(uniquebool.FALSE), "FALSE")
        
    def test_replace(self):
        case = {
            'A': (1, 5, True, False, ["b", (False, 3)]),
            'B': 0,
            'C': True,
            'D': False,
            'E': [6, "Pink Elephant", True, False, None, {True: False}],
            True: 6,
            ("a", "b"): (7, True),
        }
        expected = {
            'A': (1, 5, uniquebool.TRUE, uniquebool.FALSE, ["b", (uniquebool.FALSE, 3)]),
            'B': 0,
            'C': uniquebool.TRUE,
            'D': uniquebool.FALSE,
            'E': [6, "Pink Elephant", uniquebool.TRUE, uniquebool.FALSE, None, {True: uniquebool.FALSE}],
            # only replaces values, not keys
            True: 6,
            ("a", "b"): (7, uniquebool.TRUE),
        }
        result = uniquebool.deep_replace_bool(case)
        
        #print (case)
        #print (expected)
        #print (result)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
