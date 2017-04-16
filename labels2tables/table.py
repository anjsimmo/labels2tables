from . import uniquebool

def create_matrix(n_rows, n_cols, fill):
    # creates a 2d array of fill
    # n_rows -- number of rows
    # n_cols -- number of cols
    # fill -- value to initialize each cell with
    # returns -- list of lists
    result = []
    for i in range(0, n_rows):
        row = [fill] * n_cols
        result.append(row)
    return result

class Table:
    def __init__(self):
        self.n_cols = 0
        self.n_data_rows = 0
        self.n_header_rows = 0
        self.head = []
        # keeps traked of merged cells in header
        self.head_stretch = []
        self.data = []
        self.data_indent = []
        self.built = False

    # Table construction
    def set_cols(self, n_cols):
        self.n_cols = n_cols

    def set_data_rows(self, n_rows):
        self.n_data_rows = n_rows

    def set_header_rows(self, n_rows):
        self.n_header_rows = n_rows

    def build(self):
        # There are two types of empty-like cells:
        # * None (displayed as '-')
        # * Invisible (empty string)
        self.head = create_matrix(self.n_header_rows, self.n_cols, '')
        self.head_stretch = create_matrix(self.n_header_rows, self.n_cols, 1)
        self.data = create_matrix(self.n_data_rows, self.n_cols, '')
        self.data_indent = create_matrix(self.n_data_rows, self.n_cols, 0)
        self.built = True

    def set_row_cell(self, r, c, txt, indent=0):
        assert self.built
        self.data[r][c] = txt
        self.data_indent[r][c] = indent

    def set_header_cell(self, r, start_col, end_col, txt):
        """
        start_col -- start of merged cols (included)
        end_col -- end of merged cols (excluded)
        """
        assert self.built
        self.head[r][start_col] = txt
        self.head_stretch[r][start_col] = end_col - start_col

    # Table viewing
    def get_dims(self):
        assert self.built
        return ((self.n_header_rows, self.n_data_rows), self.n_cols)

    def iter_rows(self):
        assert self.built
        for r in self.data:
            yield r

class TableFormatter:
    """
    Graphically/Textually presents the data in a table
    """
    pass

class TxtTable(TableFormatter):
    class DimensionedTable:
        def __init__(self, table):
            # copy table functionality
            self.iter_rows = table.iter_rows
            self.get_dims = table.get_dims

            # copy table properties
            self.n_cols = table.n_cols
            self.n_data_rows = table.n_data_rows
            self.n_header_rows = table.n_header_rows
            self.head = table.head
            self.head_stretch = table.head_stretch
            self.data = table.data
            self.data_indent = table.data_indent
            self.built = table.built

            # own properties
            self.col_width = []
            for col in range(self.n_cols):
                # initialize col widths to 0
                self.col_width.append(0)

            self.min_col_right_pos = [] # minimum nuber of chars right side of col must end at.
                                        # measured as absolute position from leftmost part of table.
            for col in range(self.n_cols):
                # initialize col widths to 0
                self.min_col_right_pos.append(0)
        def get_header(self, hr, c):
            return self.display(self.head[hr][c])
        def get_cell(self, r, c):
            return self.display(self.data[r][c])
        def display(self, cell_data):
            return TxtTable._display(cell_data)

    def __init__(self):
        pass

    def present(self, table):
        """
        table -- table.Table
        returns -- table formated as text
        """
        dims = TxtTable.DimensionedTable(table)

        left_pos = 0
        # find minimum size of each column (greedily take smallest possible, starting from leftmost column)
        for c in range(0, dims.n_cols):
            for hr in range(0, dims.n_header_rows):
                cell_width = len(dims.get_header(hr, c))
                c_right_edge = c + dims.head_stretch[hr][c] - 1
                min_cell_right_pos = left_pos + cell_width
                curr = dims.min_col_right_pos[c_right_edge]
                dims.min_col_right_pos[c_right_edge] = max(curr, min_cell_right_pos)

            for r in range(dims.n_data_rows):
                cell_width = len(dims.get_cell(r, c))
                min_cell_right_pos = left_pos + cell_width
                curr = dims.min_col_right_pos[c]
                dims.min_col_right_pos[c] = max(curr, min_cell_right_pos)

            dims.col_width[c] = dims.min_col_right_pos[c] - left_pos
            left_pos = dims.min_col_right_pos[c] + 1 # include 1 char padding

        result = ""
        num_breaks = max(0, dims.n_cols - 1)
        col_total_width = sum(dims.col_width)
        table_width = col_total_width + num_breaks
        result += "=" * table_width + "\n"
        for hr in range(dims.n_header_rows):
            padded_row = []
            underlines = ""
            underline_upto = 0
            c = 0
            while c < dims.n_cols:
                stretch = dims.head_stretch[hr][c]
                contents = dims.get_header(hr, c)
                
                # any non-leaf header should be underlined, even if it only stretches over one cell
                if hr < dims.n_header_rows - 1 and contents != '':
                    # underline all cols in stretched/merged cols
                    stretch_total_width = sum(dims.col_width[c:c+stretch])
                    num_breaks = stretch - 1
                    col_width = stretch_total_width + num_breaks
                    underlines += "-" * col_width

                    padded_row.append(TxtTable._pad(contents, col_width))

                    c += stretch
                    if c < dims.n_cols:
                        underlines += " " # col separation
                else:
                    col_width = dims.col_width[c]
                    underlines += " " * col_width # no underline

                    padded_row.append(TxtTable._pad(contents, col_width))

                    c += 1
                    if c < dims.n_cols:
                        underlines += " " # col separation

            result += " ".join(padded_row) + "\n"
            if hr < dims.n_header_rows - 1: # don't attempt to underline final row
                result += underlines + "\n"
        result += "=" * table_width + "\n"
        for r in range(dims.n_data_rows):
            padded_row = []
            for c in range(dims.n_cols):
                contents = dims.get_cell(r, c)
                col_width = dims.col_width[c]
                padded_row.append(TxtTable._pad(contents, col_width))
            result += " ".join(padded_row) + "\n"
        result += "=" * table_width
        return result

    @classmethod
    def _pad(cls, s, pad_length):
        remainder = pad_length - len(s)
        assert remainder >= 0
        return s + " " * remainder

    @classmethod
    def _display(cls, td, indent=0):
        """
        td -- data to display
        returns -- string
        """
        
        # Need the types, else key False == key 0 and key True == key 1.
        conv_map = {
            (uniquebool.UniqueBool, uniquebool.TRUE): 'Y',
            (uniquebool.UniqueBool, uniquebool.FALSE): 'N',
            # Type of None is NoneType, but NoneType isn't exposed in Python3
            (type(None), None): '-'
        }
        
        if type(td) is list:
            if len(td) == 0:
                # empty list, will be represented as '-'
                td = None
            else:
                # hierarchy, display final element with indent
                indent += len(td) - 1
                td = td[-1]
        
        result = " " * indent
        key = (type(td), td)
        if key in conv_map:
            td = conv_map[key]
            result += td
        else:
            result += str(td)
        
        return result

    def cmp(self, txta, txtb):
        """
        Compares textually formatted tables for equivlence.
        Tables with different data or col names are not the same.
        Tables with extra whitespace/streched column widths
        may be accptable.

        returns -- true if tables match.
        """
        # todo: allow more flexibility
        
        # ignore any extra whitespace at end of each line
        txta = '\n'.join([l.rstrip() for l in txta.split('\n')])
        txtb = '\n'.join([l.rstrip() for l in txtb.split('\n')])
        
        return txta.strip() == txtb.strip()
