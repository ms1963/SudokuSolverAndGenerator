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

    OneCandidateLeftStrategy
    
this strategy analyzes whether there is only
one candidate left for (i,j). If yes, this 
must be the right number to fill IndentationError
#############################################################
"""
############ OneCandidateLeftStrategy ############ 
# 
from board import Board, dim, DIM
from strategy import OccupationStrategy
    
class OneCandidateLeftStrategy(OccupationStrategy): 
    def __init__(self, board):
        self.board = board
        
    def applyToQuadrant(self, i, j):
        pass
            
    def applyToColumn(self, i,j):
        pass
            
    def applyToRow(self, i, j):
        pass
    def applyStrategy(self, i, j):
        result = 0
        (x,y,z) = self.board.getElement(i,j)
        if len(z) == DIM-1:  # exactly one number is missing 
                              # in the influencer list which 
                              # needs to be the one to be put 
                              # in (i,j)
            # thus candidates has only one entry
            candidates = self.board.getCandidates(i,j)
            # the only candidate left is returned 
            return candidates[0] # return that number
        return result
            