import copy
from . import table as t
from . import uniquebool

def indent(s, amount=2):
    """
    Indents a block of text (useful for debug purposes).
    Not intended for use in indenting table cells!
    """
    results = []
    for line in s.split('\n'):
        results.append(" "*amount + line)
    return "\n".join(results)

class Node(object):
    def __init__(self, name):
        self.name = name
        self.children = []
        self.descendants = 1 # count leaf nodes as 1
        self.depth = 1
        self.parent = None
    
    def add_child(self, child):
        self.children.append(child)
        child.parent = self
    
    @property
    def child_count(self):
        return len(self.children)
    
    def update_descendants(self):
        """Updates descendant count (assumes children already updated)"""
        descendants = sum([c.descendants for c in self.children])
        self.descendants = max(1, descendants) # if leaf node, count as 1.
        self.depth = 1 + max([c.depth for c in self.children]) # max depth
    
    def recalc_descendants(self):
        """Recursively updates descendant counts (assumes acylic graph)"""
        # back up tree (in reverse order - from leaves up)
        branches = []
        sweep = [self]
        while sweep:
            sweep_next = []
            for node in sweep:
                if len(node.children) > 0:
                    branches.append(node)
                    sweep_next += node.children
            sweep = sweep_next
        
        for node in reversed(branches):
            node.update_descendants()
    
    @property
    def chain(self):
        chain = []
        node = self
        # chain back to, but not including, root node
        while node and node.parent:
            chain.append(node.name)
            node = node.parent
        chain = reversed(chain)
        return tuple(chain)
    
    def pad(self, length=None):
        """Deprecated"""
        if length == None:
            # default: pad all children to same depth
            length = self.depth
            
        # Pads all children chains with empty nodes to ensure all chains are
        # same target length.
        if length == 1:
            # When target length reaches 0, then we shouldn't have any children
            assert self.children == []
            return
            
        if self.children == []:
            # If no children, extend
            self.add_child(Node(None))

        for c in self.children:
            # Recursively pad children
            c.pad(length - 1)
    
    def __str__(self):
        result = [str(self.name)]
        result += [indent(str(c)) for c in self.children]
        return '\n'.join(result)

class HeaderNode(Node):
    pass
    
class DataNode(Node):
    def __init__(self, *args, **kwargs):
        super(DataNode, self).__init__(*args, **kwargs)
        self.row_start = None
        self.height = 1 # default partition height
    
    @property
    def val(self):
        # alias for name of node
        return self.name

def create_header_tree(cols):
    root = HeaderNode('Root')
    
    # broad pass top-down to construct tree
    current_sweep = [(root, col) for col in cols]
    while current_sweep:
        next_sweep = []

        for r, c in current_sweep:
            if type(c) is tuple:
                # sub-col c contains futher branches
                name, tail = c
                node = HeaderNode(name)
                r.add_child(node)
                
                if type(tail) is list:
                    # c hss multiple branches
                    for child in tail:
                        next_sweep.append((node, child))
                else:
                    # c has only one branch
                    next_sweep.append((node, tail))
            elif type(c) is list:
                raise Exception('Expected tuple or string')
            else:
                # c is leaf
                node = HeaderNode(c)
                r.add_child(node)

        current_sweep = next_sweep
    
    root.recalc_descendants() # todo, make Node class automatically update counts.
    
    # root with all elements connected, and descendants counted
    return root

def set_headers(cols, data, table):
    header_tree = create_header_tree(cols)
    table_cols = header_tree.descendants
    num_header_rows = header_tree.depth - 1 # don't include root node
    
    # Depth first search for child nodes.
    # note that it is important that cols come out in correct order!
    leaves = []
    
    def visit(r, c, node):
        # r,c r,c args will be oriented wrong way,
        # but we only care about the node
        if not node.children:
            leaves.append(node)
    
    # walk tree and fill table cells
    walk_tree(
        header_tree, # walk_tree is intended for walking row_tree,
                     # but can also walk col_headers
                     # (but visit r,c args will be oriented wrong way)
        visit
    )
    
    # set cols to just the final leaves
    col_chains = [leaf.chain for leaf in leaves]
    
    return header_tree, col_chains, table_cols, num_header_rows
    
def fill_headers(tree, table):
    """
    tree -- header_tree returned from set_headers
    table -- built Table
    return -- col_leaves
    """

    leaves = []
    
    # sweep tree top to bottom, left to right.
    depth = 0
    current_sweep = tree.children
    while current_sweep:
        cols_to_left = 0
        next_sweep = []
        for node in current_sweep:
            end_col = cols_to_left + node.descendants           
            if depth < tree.depth - 1 - node.depth:
                # column hierarchy is shorter than others
                # add vertical padding and come back next sweep
                next_sweep.append(node)
                cols_to_left = end_col
            else:
                txt = node.name
                table.set_header_cell(depth, cols_to_left, end_col, txt)
                cols_to_left = end_col
                for child in node.children:
                    next_sweep.append(child)
                if not node.children:
                    leaves.append(node)
        depth += 1
        current_sweep = next_sweep
    
    # leaves are col names
    return leaves

def create_data_tree(cols, data):
    """
    cols -- col_chains returned by set_headers
    data -- tags data
    """
    root = DataNode('Root')
    root.row_start = 0
    root.height = len(data) # root partition contains all data rows
                            # this will later be sub-partitioned
    sweep = [root]
    
    for c, col_name in enumerate(cols):
        # Split up data into horizontal partitions.
        # Consecutive rows with the same col value will be placed in the same partition
        next_sweep = []
        
        for partition in sweep:
            rstart = partition.row_start
            rend   = rstart + partition.height
            
            sub_partition = None
            hierarchy_context = [] # Current hierarchy context.
                                   # Used to decide whether to insert
                                   # special hierarchy partition row
            
            for r in range(rstart, rend):
                rdata = data[r]

                # lookup cell data for this row, column
                try:
                    cdata = fuzzy_row_lookup(rdata, col_name)
                except KeyError:
                    cdata = None
                
                if type(cdata) is list:
                    # hierarchy
                    diff_index = 0
                    
                    while diff_index < min(len(cdata)-1, len(hierarchy_context)):
                        if cdata[diff_index] == hierarchy_context[diff_index]:
                            diff_index += 1
                        else:
                            # diff_index will be the first index where
                            # desired hierarchy context differs from last
                            # hierarchy context
                            break
                    
                    for level in cdata[diff_index:-1]:
                        # insert header for level
                        # Start a new partition for this row
                        sub_partition = DataNode(level)
                        sub_partition.row_start = r
                        sub_partition.height = 0
                        partition.add_child(sub_partition)
                        next_sweep.append(sub_partition)
                    
                    hierarchy_context = cdata[:-1]
                
                # every row in last column is always its own partition
                # (prevents creating rows that are completely blank / missing).
                if sub_partition != None and cdata == sub_partition.val and c != len(cols)-1:
                    # Repeated value in this column.
                    # Merge this cell into the last group.
                    sub_partition.height += 1
                else:
                    # Start a new partition for this row
                    sub_partition = DataNode(cdata)
                    sub_partition.row_start = r
                    partition.add_child(sub_partition)
                    next_sweep.append(sub_partition)
        
        sweep = next_sweep
    
    root.recalc_descendants() # todo, make Node class automatically update counts.

    # root node with all partitions attached
    return root

def setup_data_cels(col_chains, data):
    """
    col_chains -- col_chains leaves returned by set_headers
    data -- tags data
    retrn -- data_tree, num_rows
    """
    data_tree = create_data_tree(col_chains, data)
    num_rows = data_tree.descendants
    return data_tree, num_rows

def fill_data_cels(table, row_tree):
    """
    table    -- built table
    row_tree -- return value of setup_data_cels
    """
    def visit(r, c, node):
        table.set_row_cell(r, c, node.val)
        
    # walk tree and fill table cells
    walk_tree(
        row_tree,
        visit
    )

def walk_tree(tree, visit_func):
    """
    Depth-first walk of tree of Nodes.
    r,c indexes are under assumption of walking row_tree from left to right
    (to remove duplicate rows).
    tree -- root Node
    visit_func -- lambda r, c, node
    """
    # walk the tree
    r = 0
    c = 0
    # path depth -> list of children
    unvisited = [] # list of list of children seen at each node in path.
                  # TODO: Use doubly linked list for efficiency.
    unvisited.append(list(tree.children))

    while True:
        #print 'walk {}'.format((r,c))
        
        unvisited_children = unvisited[-1]
        if len(unvisited_children) > 0:
            # dive in
            node = unvisited_children.pop(0)
            unseen = list(node.children)
            unvisited.append(unseen)
            
            # visit code here
            visit_func(r, c, node)
            # end visit code
            
            # track position
            c += 1
        else:
            # backtrack
            while len(unvisited_children) == 0:
                unvisited.pop()
                
                if len(unvisited) == 0:
                    # seen everything
                    return
                
                unvisited_children = unvisited[-1]
                # track position
                c -= 1
            
            # track position
            r += 1

def fuzzy_row_key(rdata, col):
    """
    Lookup correct index using closest col name.
    If the col has trailing Nones, these are ignored
    return -- key
    """
    # Todo: Normalize rdata first
    
    try:
        # Remove trailing Nones.
        col = col[:col.index(None)]
    except ValueError:
        # No trailing Nones. Leave col as is.
        pass
    
    if len(col) == 1:
        # For non-hierarchical cols, allow just string (e.g. "Sweet")
        # rather than packing as tupple.
        col = col[0]
    
    return col
    
def fuzzy_row_lookup(rdata, col):
    """
    Lookup row data using closest col name.
    If the col has trailing Nones, these are ignored
    """
    # Todo: Normalize rdata first
    
    col = fuzzy_row_key(rdata, col)

    # will throw a KeyError if not present
    cdata = rdata[col]
    return cdata

def normalize_table(col_chains, data, types):
    """
    Normalize data in table to make processing simpler
    col_chains -- from set_headers
    data -- table input data array
    types -- table input type array
    return -- data_norm, the normalized data array
    """
    # Currently:
    # * Normalize hierarchies (ensure consistent level depths)
    # Todo: fill in missing cells
    
    data_norm = copy.deepcopy(data)
    
    # Set missing cells in bool cols to False
    for c, col_name in enumerate(col_chains):
        if types[c] == 'bool':
            for r, rdata in enumerate(data):
                
                col_norm = fuzzy_row_key(rdata, col_name)
                
                try:
                    cdata = rdata[col_norm]
                except KeyError:
                    # missing data => convert to False
                    cdata = uniquebool.FALSE
                
                data_norm[r][col_norm] = cdata
    
    # Normalize hierarchies
    for c, col_name in enumerate(col_chains):
        hierarchy_headers = set()
        
        # find hierarchical cols
        for r, rdata in enumerate(data):
            
            try:
                cdata = fuzzy_row_lookup(rdata, col_name)
            except KeyError:
                cdata = None
            
            if type(cdata) is list:
                key = tuple(cdata)
                hierarchy_headers.add(key)
        
        # old header -> new length
        header_lengths = dict()
        
        # find ideal header lengths
        for header in hierarchy_headers:
            # pad any main headers above this header
            # to be at least the length of this header.
            # e.g., if there is a A.B header,
            # then push any data for the A header into A.-
            sub_headers = []
            
            for i in range(1, len(header)+1):
                sub_header = header[0:i]
                sub_headers.append(sub_header)
            
            for sub_header in sub_headers:
                if sub_header not in header_lengths:
                    header_lengths[sub_header] = 0 # initialize

                header_lengths[sub_header] = max(header_lengths[sub_header], len(header))
        
        # pad headers
        for r, rdata in enumerate(data):
            
            col_norm = fuzzy_row_key(rdata, col_name)
            
            try:
                cdata = rdata[col_norm]
            except KeyError:
                cdata = None

            if type(cdata) is list:
                key = tuple(cdata)
                
                if key in header_lengths:
                    pad_len = header_lengths[key]
                    # pad header with Nones to make correct length
                    pad_diff = pad_len - len(cdata)
                    assert pad_diff >= 0
                    cdata_new = cdata + [None] * pad_diff                    
                    #print ('old {} new {}'.format(cdata, cdata_new))
                    
                    # use row_new
                    data_norm[r][col_norm] = cdata_new
    
    return data_norm

def infer_type(col_chains, types, data):    
    for c, col_name in enumerate(col_chains):
        if types[c] != None:
            # already set
            continue
        
        bool_count = 0
        empty_count = 0
        other_count = 0

        # find hierarchical cols
        for r, rdata in enumerate(data):
            try:
                cdata = fuzzy_row_lookup(rdata, col_name)
            except KeyError:
                cdata = None
            
            if cdata == None:
                empty_count += 1
            elif type(cdata) is uniquebool.UniqueBool:
                bool_count += 1
            else:
                other_count += 1
        
        if other_count > 0:
            # non-boolean. Assume text.
            # Empty => '-'
            types[c] = 'str'
        else:            
            # Default to assuming bool
            # Empty => 'F'
            types[c] = 'bool'

    return types

def tags2table(table_arg):
    """
    See examples for how to specify table_arg
    table_arg -- dict of data and cols
    return -- Table
    """
    table = t.Table()
    data = table_arg['data']
    cols = table_arg['cols']
    
    # Replace pesky True, False objects with our own uniquebool.TRUE, uniquebool.FALSE
    # objects. This prevents partitioning issues due to True == 1.
    data = uniquebool.deep_replace_bool(data)

    header_tree, col_chains, table_cols, num_header_rows = set_headers(cols, data, table)

    if not 'types' in table_arg:
        table_arg['types'] = [None] * table_cols
    
    types = table_arg['types']
    assert len(types) == table_cols
    # Attempt to infer unspecified types from data
    types = infer_type(col_chains, types, data)
    
    data = normalize_table(col_chains, data, types)
    row_tree, num_rows = setup_data_cels(col_chains, data)

    table.set_cols(len(col_chains))
    table.set_header_rows(num_header_rows)
    table.set_data_rows(num_rows)
    table.build()

    fill_headers(header_tree, table)
    fill_data_cels(table, row_tree)

    return table
