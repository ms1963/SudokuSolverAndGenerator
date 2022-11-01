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

    SwordFishStrategy
     
#############################################################
"""
############ Swordfish Strategy ################ 

from board import Board, dim, DIM
from strategy import InfluenceStrategy

class SwordFishStrategy(InfluenceStrategy):
    def __init__(self, board):
        self.board = board
    
    # check how often the pivot appears in the row
    def rowContainsCandidate(self, pivot, r):
        result = 0
        # search in all columns
        for c in range(1, DIM+1):
            (x,y,z) = self.board.getElement(r,c)
            if x: continue # continue when occupied
            if pivot in self.board.getCandidates(r,c):
                result += 1
        return result

    # check how often the pivot appears in the column
    def columnContainsCandidate(self, pivot, c):
        # search in all rows
        for r in range(1, DIM+1):
            result = 0
            (x,y,z) = self.board.getElement(r,c)
            if x: continue # continue when occupied
            if pivot in self.board.getCandidates(r,c):
                result += 1
        return result

    # checks for the three columns specified 
    # in which rows the pivot can be found
    def matchingRows(self, pivot, c1, c2, c3):
        rowList = []
        # search in all rows where pivot is a candidate 
        for r in range(1,DIM+1):
            if (pivot in self.board.getCandidates(r, c1)) or (pivot in self.board.getCandidates(r, c2)) or (pivot in self.board.getCandidates(r, c3)):
                rowList.append(r)
        return rowList

    # checks for the three rows specified 
    # in which columns the pivot can be found
    def matchingColumns(self, pivot, r1, r2, r3):
        colList = []
        # search in all columns where pivot is a candidate 
        for c in range(1,DIM+1):
            if (pivot in self.board.getCandidates(r1, c)) or (pivot in self.board.getCandidates(r2, c)) or (pivot in self.board.getCandidates(r3, c)):
                colList.append(c)
        return colList

    # for all pivots and all configurations of 3 columns where
    # the pivot is found 2 or 3 times as a candidate, it is checked
    # whether there are only three rows in which the pivot is a 
    # candidate. If yes, SwordFisgh can be applied by removing
    # the candidates from these rows which are not in one of 
    # the columns
    def applyStrategyToColumns(self):
        for pivot in range(1, DIM+1):
            for c1 in range(1, DIM-1):
                howMany = self.columnContainsCandidate(pivot, c1)
                if howMany <= 1 or howMany > dim: continue
                for c2 in range(c1+1, DIM):
                    howMany = self.columnContainsCandidate(pivot, c2)
                    if howMany <= 1 or howMany > dim: continue
                    for c3 in range(c2+1, DIM+1):
                        howMany = self.columnContainsCandidate(pivot, c3)
                        if howMany <= 1 or howMany > dim: continue
                        rowList = self.matchingRows(pivot,c1,c2,c3)
                        if len(rowList) == dim:
                            for r in rowList:
                                self.board.addInfluencerToRow(pivot, r, [c1, c2, c3])

    # for all pivots and all configurations of 3 rows where
    # the pivot is found 2 or 3 times as a candidate, it is checked
    # whether there are only three columns in which the pivot is a 
    # candidate. If yes, SwordFisgh can be applied by removing
    # the candidates from these columns which are not in one of 
    # the rows
    def applyStrategyToRows(self):
        for pivot in range(1, DIM+1):
            for r1 in range(1, DIM-1):
                howMany = self.rowContainsCandidate(pivot, r1)
                if howMany <= 1 or howMany > dim: continue
                for r2 in range(r1+1, DIM):
                    howMany = self.rowContainsCandidate(pivot, r2)
                    if howMany <= 1 or howMany > dim: continue
                    for r3 in range(r2+1, DIM+1):
                        howMany = self.rowContainsCandidate(pivot, r3)
                        if howMany <= 1 or howMany > dim: continue
                        colList = self.matchingColumns(pivot,r1,r2,r3)
                        if len(colList) == dim:
                            for c in colList:
                                self.board.addInfluencerToColumn(pivot, c, [r1, r2, r3])

    def applyStrategy(self):
        self.applyStrategyToColumns()
        self.applyStrategyToRows()