"""Easy context-based interface for generating a sheet and cells.

Comparible to matplotlib pylab interface, this interface keeps track of the current
sheet. Using the :ref:`cell` function, :ref:`Cell` widgets are added to the current sheet.


"""
__all__ = ['sheet', 'current', 'cell', 'calculation', 'row', 'column', 'cell_range', 'hold_cells']
import copy
import numbers

import ipywidgets as widgets
from .sheet import *
_last_sheet = None
_sheets = {} # maps from key to Sheet instance
_hold_cells = False # when try (using hold_cells() it does not add cells directly)
_cells = () # cells that aren't added directly

def sheet(key=None, rows=5, columns=5, column_width=None, row_headers=True, column_headers=True,
        stretch_headers='all', **kwargs):
    """Creates a new Sheet instance or retrieves one registered with key, and sets this as the 'current'.

    If the key argument is given, and no sheet is created before with this key, it will be registered under
    this key. If this function is called again with the same key argument, that :ref:`Sheet` instance
    will be returned.

    Example:

    >>> sheet1 = ipysheet.sheet('key1')
    >>> sheet2 = ipysheet.sheet('key2')
    >>> assert sheet2 is ipysheet.current()
    >>> assert sheet1 is ipysheet.sheet('key1')
    >>> assert sheet1 is ipysheet.current()
 
    Parameters
    ----------
    key : any
        If not used before, register the sheet under this key. If used before, return the previous `Sheet` instance 
        registered with this key.

    Returns
    -------
    Sheet
        The new sheet, or if key is given, the previously created sheet registered with this key.

    """
    global _last_sheet
    if isinstance(key, Sheet):
        _last_sheet = key
    elif key is None or key not in _sheets:
        _last_sheet = Sheet(rows=rows, columns=columns, column_width=column_width,
        row_headers=row_headers, column_headers=column_headers,
        stretch_headers=stretch_headers, **kwargs)
        if key is not None:
            _sheets[key] = _last_sheet
    else:
        _last_sheet = _sheets[key]
    return _last_sheet

def current():
    """Returns the current `Sheet` instance"""
    return _last_sheet

def cell(row, column, value=0., type=None, color=None, backgroundColor=None,
    fontStyle=None, fontWeight=None, style=None, label_left=None, choice=None,
    read_only=False, format='0.[000]', renderer=None):
    """Adds a new `Cell` widget to the current sheet

    Parameters
    ----------
    row : int
        Zero based row index
    column : int
        Zero based column index
    type : string
        Type of cell, options are: text, numeric, checkbox, dropdown, numeric, date.
        If type is None, the type is inferred from the type of the value being passed,
        numeric (float or int type), boolean (bool type), or else text. When choise is given
        the type will be assumed to be dropdown.
        The types refer (currently) to the handsontable types:
          https://docs.handsontable.com/0.35.1/demo-custom-renderers.html



    """
    global _cells
    if type is None:
        if isinstance(value, bool):
            type = 'checkbox'
        elif isinstance(value, numbers.Number):
            type = 'numeric'
        else:
            type = 'text'
        if choice is not None:
            type = 'dropdown'

    style = style or {}
    if color is not None:
        style['color'] = color
    if backgroundColor is not None:
        style['backgroundColor'] = backgroundColor
    if fontStyle is not None:
        style['fontStyle'] = fontStyle
    if fontWeight is not None:
        style['fontWeight'] = fontWeight
    c = Cell(value=value, row=row, column=column, type=type, style=style,
        read_only=read_only, choice=choice, renderer=renderer, format=format)
    if _hold_cells:
        _cells += (c,)
    else:
        _last_sheet.cells = _last_sheet.cells+(c,)
    if label_left:
        assert column-1 >= 0, "cannot put label to the left"
        cell(row, column-1, value=label_left, fontWeight='bold')
    return c

def row(row, value, column_start=0, column_end=None):
    """Create a Range widget, representing multiple cells in a sheet, in a horizontal row

    Parameters
    ----------
    row : int
        Which rows, 0 based.
    value : list
        List of values for each cell.
    column_start : int
        Which column the row will start, default 0.
    column_end : int
        Which column the row will end, default is the last.

    Returns
    -------
    Range
        A range widget.

    """
    if column_end is None:
        column_end = column_start+len(value)
    length = column_end - column_start
    print(length, len(value))
    if length != len(value):
         raise ValueError("length or array doesn't match number of columns")
    if column_start + length >_last_sheet.columns:
         raise ValueError("array will go outside of sheet, too many columns")
    cellrange = Range(value=value)
    column_indices = range(column_start, column_end)
    cells = [cell(row, i, value[i-column_start]) for i in column_indices]
    for i, cell_offset in zip(column_indices, cells):
        def set(change, cell_offset=cell_offset, column=i):
            offset = column - column_start
            value = copy.deepcopy(cellrange.value)
            value[offset] = cell_offset.value
            cellrange.value = value
        cell_offset.observe(set, 'value')
    def set(*ignore):
        value = cellrange.value
        for i, cell_offset in enumerate(cells):
            cell_offset.value = value[i]
    cellrange.observe(set)
    return cellrange

def column(column, value, row_start=0, row_end=None):
    """Create a Range widget, representing multiple cells in a sheet, in a horizontal column

    Parameters
    ----------
    column : int
        Which rows, 0 based.
    value : list
        List of values for each cell.
    row_start : int
        Which row the column will start, default 0.
    row_end : int
        Which row the column will end, default is the last.

    Returns
    -------
    Range
        A range widget.

    """
    if row_end is None:
        row_end = row_start+len(value)
    length = row_end - row_start
    print(length, len(value))
    if length != len(value):
         raise ValueError("length or array doesn't match number of rows")
    if row_start + length >_last_sheet.rows:
         raise ValueError("array will go outside of sheet, too many rows")
    cellrange = Range(value=value)
    row_indices = range(row_start, row_end)
    cells = [cell(i, column, value[i-row_start]) for i in row_indices]
    for i, cell_offset in zip(row_indices, cells):
        def set(change, cell_offset=cell_offset, row=i):
            offset = row - row_start
            value = copy.deepcopy(cellrange.value)
            value[offset] = cell_offset.value
            cellrange.value = value
        cell_offset.observe(set, 'value')
    def set(*ignore):
        value = cellrange.value
        for i, cell_offset in enumerate(cells):
            cell_offset.value = value[i]
    cellrange.observe(set)
    return cellrange

def _transpose(list_of_lists):
    return [list(k) for k in zip(*list_of_lists)]

def cell_range(value, row_start=0, column_start=0, row_end=None, column_end=None, transpose=False, return_cells=False):
    """Create a Range widget, representing multiple cells in a sheet, in a horizontal column

    Parameters
    ----------
    value : list of lists
        List of lists values for each cell.
    row_start : int
        Which rows to start, 0 based.
    column_start : int
        Which rows to start, 0 based.
    row_end : int
        Which row the column will end, default is the last.
    column_end : int
        Which row the column will end, default is the last.

    Returns
    -------
    Range
        A range widget.

    """
    # instead of if statements, we just use T to transpose or not when needed
    T = (lambda x: x) if not transpose else _transpose
    # we work with the optionally transposed values for simplicity
    value = T(value)
    print(value)
    if row_end is None:
        row_end = row_start+len(value)
    row_length = row_end - row_start
    if row_length != len(value):
         raise ValueError("length or array doesn't match number of rows")
    if row_length == 0:
         raise ValueError("0 rows not supported")
    if column_end is None:
        column_end = column_start+len(value[0])
    column_length = column_end - column_start
    if column_length == 0:
         raise ValueError("0 columns not supported")
    for row in value:
        if column_length != len(row):
            raise ValueError("not a regular matrix, columns lengths differ")
    if row_start + row_length >_last_sheet.rows:
         raise ValueError("array will go outside of sheet, too many rows")
    if column_start + column_length >_last_sheet.columns:
         raise ValueError("array will go outside of sheet, too many columns")
    cellrange = Range(value=T(value))
    row_indices = range(row_start, row_end)
    column_indices = range(column_start, column_end)
    cells = [[cell(i, j, value[i-row_start][j-column_start]) for j in column_indices] for i in row_indices]
    #for i, cell_offset in zip(row_indices, cells):
    for i in row_indices:
        for j in column_indices:
            cell_ = cells[i - row_start][j - column_start]
            def set(change, cell_=cell_, row=i, column=j):
                row_offset = row - row_start
                column_offset = column - column_start
                value = copy.deepcopy(T(cellrange.value))
                value[row_offset][column_offset] = cell_.value
                print('change', cellrange.value, 'to', value)
                cellrange.value = T(value)
            cell_.observe(set, 'value')
    def set(*ignore):
        value = T(cellrange.value)
        print('update', *ignore)
        for i in row_indices:
            for j in column_indices:
                cells[i][j].value = value[i][j]
    cellrange.observe(set)
    if return_cells:
        return cellrange, cells
    else:
        return cellrange



def _assign(object, value):
    if isinstance(object, widgets.Widget):
        object, trait = object, 'value'
    else:
        object, trait = object
    setattr(object, trait, value)

def calculation(inputs, output, initial_calulation=True):
    def decorator(f):
        def calculate(*ignore_args):
            values = [getattr(input, 'value') for input in inputs]
            result = f(*values)
            _assign(output, result)
        for input in inputs:
            input.observe(calculate, 'value')
        if initial_calulation:
            calculate()
    return decorator

from contextlib import contextmanager
@contextmanager
def hold_cells():
    """Hold adding any cell widgets until leaving this context.

    This may give a better performance when adding many cells.
    
    Example
    -------

    >>> ipsheet.sheet(rows=10,columns=10)
    >>> with ipysheet.hold_cells()
    >>>  for i in range(10):
    >>>    for j in range(10):
    >>>      ipysheet.cell(i,j, value=i*10+j)
    >>> # at this line, the Cell widgets are added
    """
    global _hold_cells
    global _cells
    if _hold_cells is True:
        yield
    else:
        try:
            _hold_cells = True
            yield
        finally:
            _hold_cells = False
            #print(_cells, _last_sheet.cells)
            _last_sheet.cells = tuple(_last_sheet.cells) + tuple(_cells)
            _cells = ()
