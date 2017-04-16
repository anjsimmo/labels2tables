import unittest
import labels2tables.tags2table as t2t
import tests.sample_utils as utils
import labels2tables.table as t
import os

class TestTagsToTable(unittest.TestCase):
    def setUp(self):
        d = os.path.dirname(__file__)
        self.test_dir = os.path.normpath(os.path.join(d, '../examples/'))
    
    def test_samples(self):
        """
        run all "functional tests" in sample directory
        """
        for sub_file in sorted(os.listdir(self.test_dir)):
            if not sub_file.endswith('.spec.txt'):
                continue
            
            test_file = os.path.join(self.test_dir, sub_file)
            sample = utils.load_sample(test_file)
            sample_arg = sample.arg
            table = t2t.tags2table(sample_arg)
            presenter = t.TxtTable()
            actual_txt = presenter.present(table)
            expected_txt = sample.txt
            result = presenter.cmp(actual_txt, expected_txt)
            
            if result != True:
                print("==EXPECTED==")
                print(expected_txt)
                #print(expected_txt.replace('\n', '\\n\n')) # show newlines
                print("==ACTUAL==")
                print(actual_txt)
                #print(actual_txt.replace('\n', '\\n\n')) # show newlines
                #print("==RESULT==")
                #print(result)
            
            self.assertTrue(result, msg=sample.fname)

if __name__ == '__main__':
    unittest.main()
