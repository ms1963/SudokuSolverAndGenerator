
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

    Cheating
    
this strategy just searches whether a given
cell is unoccupied. If that is the case it 
looks up the number in a brute force solution
     
#############################################################
"""

############ Cheating ############ 

    
from board import Board
from strategy import OccupationStrategy

class Cheating(OccupationStrategy): 
    def __init__(self, board):
        self.board = board
            
    def applyToQuadrant(self, i, j):
        pass
            
    def applyToColumn(self, i,j):
        pass
            
    def applyToRow(self, i, j):
        pass
            
    def applyStrategy(self, i, j):
        (x,y,z) = self.board.getElement(i,j)
        if not x:
            # calculating index 
            idx = self.board.map(i,j)
            # looking up solution in brute force table:
            return int(self.board.solution[idx])     