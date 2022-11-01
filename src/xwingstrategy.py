"""
Distributed with:
GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007



#############################################################
Sudoku Solver and Generator, (c) 2022 by Michael Stal
contains the classes SudokuSolver and SudokuGenerator
requires: Python version >= 3.10
-------------------------------------------------------------
applicable to standard Sudoku board with 9 x 9 positions and
digits in {1,2, ..., 9}
=============================================================
This package consist of the classes

    XWingStrategy
    
This strategy identifies two rows (or two columns) where
there are only two cells left which can be occupied with
a number called pivot. If these cells are also aligned
with respect to their columns (or rows) and build a 
rectangular formation, a so-called X-Wing, then we know
that in the two columns (or rows) we can remove the pivot
as a candidate from the aforementioned columns (or rows)

     
#############################################################
"""


from board import Board, DIM, dim
from strategy import InfluenceStrategy

class XWingStrategy(InfluenceStrategy):
    def __init__(self, board):
        self.board = board
        
    # find all cells in row r which contain the pivot element
    def findCandidatesInRow(self,pivot, r):
        listOfCellsInARow = []
        for c in range(1, DIM+1): # check all columns 
            (x,y,z) = self.board.getElement(r,c)
            if not x: # vacant cell
                if not pivot in z: # <=> pivot in candidates
                    listOfCellsInARow.append((r, c))
        return listOfCellsInARow

    # find all cells in column c which contain the pivot element
    def findCandidatesInColumn(self,pivot, c):
        listOfCellsInAColumn = []
        for r in range(1, DIM+1): # check all rows
            (x,y,z) = self.board.getElement(r,c)
            if not x: # vacant cell
                if not pivot in z: # <=> pivot in candidates
                    listOfCellsInAColumn.append((r, c))
        return listOfCellsInAColumn

    # find X-Wings defined by rows
    def applyStrategyToRows(self):
        numbers = [n for n in range(1, DIM+1)]
        for pivot in numbers: # search for all possible numbers as pivots
            listOfCellsInARow = []
            listOfRows = []
            for r in range(1, DIM+1): # iterate through all rows r
                # get all cells in r which contain pivot
                listOfCellsInARow = self.findCandidatesInRow(pivot, r)
                # if there are only two cells in r that have pivot 
                # as a candidate
                # we found a candidate row
                if len(listOfCellsInARow) == 2: # we need rows with 2 cells
                    listOfRows.append(listOfCellsInARow)
            # only if there are at least two 
            # candidate rows we can search for possible 
            # X-Wing formations
            if len(listOfRows) >= 2:
                xWingList = self.searchForXWingRows(listOfRows)
                for xWing in xWingList: # iterate through all 
                                        # XWings found which are diagonals
                    (r11,c11,r22,c22) = xWing # diagonal with (r11,c11) as
                                 # upper left and (r22,c22) as lower right
                    exceptionList= [r11, r22] # rows not to add influencer
	
                    # add Influencer == pivot to column c11
                    self.board.addInfluencerToColumn(pivot, c11, exceptionList)
                    # add Influencer == pivot to column c22
                    self.board.addInfluencerToColumn(pivot, c22, exceptionList)

    # # find X-Wings defined by columns        
    def applyStrategyToColumns(self):
        numbers = [n for n in range(1, DIM+1)]
        for pivot in numbers: # search for all possible numbers as pivots
            listOfCellsInAColumn = []
            listOfColumns = []
            for c in range(1, DIM+1): # iterate through all rows c
                # get all cells in r which contain pivot
                listOfCellsInAColumn = self.findCandidatesInColumn(pivot, c)
                # if there are only two cells in c that 
                # have pivot as a candidate
                # we found a candidate row
                if len(listOfCellsInAColumn) == 2: # we need columns 
                                                    # with 2 cells
                    listOfColumns.append(listOfCellsInAColumn)
            # only if there are at least 2 candidate rows we can search 
            # for possible X-Wing formations
            if len(listOfColumns) >= 2:
                xWingList = self.searchForXWingColumns(listOfColumns)
                for xWing in xWingList: # iterate through all XWings  
                                        # which are diagonals
                    
                    (r11,c11,r22,c22) = xWing 
                    exceptionList= [c11, c22] # rows not to add influencer
	
                    # add Influencer == pivot to column c11
                    self.board.addInfluencerToRow(pivot, r11, exceptionList)
                    # add Influencer == pivot to column c22
                    self.board.addInfluencerToRow(pivot, r22, exceptionList)

    # listOfColumns contains all columns with only two cells 
    # where pivot is a candidate
    def searchForXWingColumns(self, listOfColumns):
        xWings = []
        # iterate through all columns with two pivot cells
        for k in range(0, len(listOfColumns)-1):
            for l in range(k+1, len(listOfColumns)): # take 2 columns
                col1Pair = listOfColumns[k]
                col2Pair  = listOfColumns[l]
                xWing  =  self.getXWingColumn(col1Pair, col2Pair)
                if xWing != None: # if we got two columns with 
                                    # cells aligned in the same rows
                    xWings.append(xWing) # add the XWing to the result
        return xWings

    # listOfRows contains all columns with only two cells where 
    # pivot is a candidate
    def searchForXWingRows(self, listOfRows):
        xWings = []
        # iterate through all rows with two pivot cells
        for k in range(0, len(listOfRows)-1):
            for l in range(k+1, len(listOfRows)): # take two of the rows
                row1Pair  = listOfRows[k]
                row2Pair  = listOfRows[l]
                xWing  =  self.getXWingRow(row1Pair, row2Pair)
                if xWing != None:   # if we got 2 rows with cells aligned 
                                    # in the same columns
                    xWings.append(xWing) # add the XWing to the result
        return xWings

    # if the cells are aligned in same columns, we got an X-Wing formation
    def getXWingRow(self, rowAPair, rowBPair):
        ((r11,c11),(r12,c12)) = rowAPair
        ((r21,c21),(r22,c22)) = rowBPair
        if (c11 == c21) and (c12 == c22):
            return (r11, c11, r22, c22)
        else:
            return None

    # if the cells are aligned in same rows, we got an X-Wing formation
    def getXWingColumn(self, colAPair, colBPair):
        ((r11,c11),(r12,c12)) = colAPair
        ((r21,c21),(r22,c22)) = colBPair
        if (r11 == r21) and (r12 == r22):
            return (r11, c11, r22, c22)
        else:
            return None
            
    # apply strategy to columns and rows
    def applyStrategy(self):
        self.applyStrategyToColumns()
        self.applyStrategyToRows()
        
