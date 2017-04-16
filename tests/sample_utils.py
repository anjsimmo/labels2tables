import json
import ast

class Sample:
    def __init__(self):
        # command to generate table
        self.arg = None
        # table that should be generated
        self.txt = ""
        self.fname = ""

def load_sample(test_file):
    """
    test_file -- path to sample
    return -- Sample
    """
    sample = Sample()
    sample.fname = test_file
    with open(test_file) as f:
        test_str = f.read()
    test_str = test_str.strip() # ignore any leading/trailing newlines, etc.
    parts = test_str.split('\n\n') # each part of test file is separated by a blank line
    assert len(parts) == 2, "Expected 2 parts, found " + str(len(parts)) + " in " + str(test_file)
    sample.txt = parts[0].strip()
    arg_txt = parts[1].strip()
    # safely parse dict from string
    sample.arg = ast.literal_eval(arg_txt)
    return sample
