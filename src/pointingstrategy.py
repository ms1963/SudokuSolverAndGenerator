
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

    PointingPairsAndTriplesStrategy
    
The class PointingPairsAndTriplesStrategy implements an 
Influence Strategy. If only 2 (or 3) cells in a quadrant 
have the candidate c and f all these cells are located
in the same row (or column), then c cannot be a candidate
in any remaining cells of this row (or column).
In contrast to other strategies this stratgey is 
provided as an external class instead of an internal
class of SudokuSolver.
    

#############################################################
"""

from strategy import InfluenceStrategy
from board import Board, DIM, dim

class PointingPairsAndTriplesStrategy(InfluenceStrategy):
    def __init__(self, board):
        self.board = board
        
    def applyStrategy(self):
        self.applyStrategyToQuadrants()
        
    def applyStrategyToQuadrants(self):
        for num in range(1, DIM+1):
            for d1 in range (1, dim+1):
                for d2 in range(1,dim+1):
                    cells = self.board.getQuadrant(d1,d2)
                    self.handlePointingPairsAndTriples(cells, num)
        
    def handlePointingPairsAndTriples(self, cells, num):
        assert len(cells) == DIM, "Error: array must have " + str(DIM) + " cells"
        cand = []
        occurrences = []
        # go through all cells in the array
        for idx in range(0, DIM):
            # if n is part of the cell
            i,j = cells[idx]
            cand = self.board.getCandidates(i,j)
            if num in cand:
                # append the cell to occurrences
                occurrences.append(cells[idx])
        # if the number does not appear in  2 or 3 cells
        count = len(occurrences)
        if not count in range(2, 3+1):
            return
        else:
            inSameRow = True 
            inSameCol = True
            c1i = 0
            c1j = 0
            c2i = 0
            c2j = 0
            c3i = 0
            c3j = 0
                
            if count == 2:
                cell1 = occurrences[0]
                cell2 = occurrences[1]
                c1i, c1j = cell1
                c2i, c2j = cell2
                inSameRow = inSameRow and (c1i == c2i)
                inSameCol = inSameCol and (c1j == c2j)
                    
            if count == 3:
                cell3 = occurrences[2]
                c3i, c3j = cell3
                inSameRow = inSameRow and (c2i == c3i)
                inSameCol = inSameCol and (c2j == c3j)
            
            (d1,d2,r,c) = self.board.inverseMapQuadrant(c1i, c1j)
            if inSameRow:
                low  = (d2-1)*dim + 1
                high = (d2-1)*dim + 3
                row = c1i
                for c in range(1, DIM+1):
                    if c >= low or c <= high: continue
                    self.board.addInfluencer(num, row, c)
            elif inSameCol:
                low  = (d1-1)*dim + 1
                high = (d1-1)*dim + 3
                col = c1j
                for r in range(1, DIM+1):
                    if r >= low or r <= high: continue
                    self.board.addInfluencer(num, r, col)