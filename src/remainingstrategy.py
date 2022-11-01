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

    RemainingInfluencersStrategy
    
this strategy searches for other vacant cells 
and checks whether there is an influencer that 
appears in all of these vacant cells. Since 
the number can not be a candidate in all 
other vacant cells, it must be the number that 
should be put into (i,j)
    

#############################################################
"""

######### RemainingInfluencerStrategy #########           


from board import Board, DIM, dim
from strategy import OccupationStrategy

class RemainingInfluencerStrategy(OccupationStrategy): 
    def __init__(self, board):
        self.board = board
        
    def applyToQuadrant(self, i, j):
        candidates = self.board.getCandidates(i,j)
        (d1, d2, r, c) = self.board.inverseMapQuadrant(i,j)
        vacancies  = self.board.getVacanciesInQuadrant(d1,d2,r,c)
        totalSet = {1,2,3,4,5,6,7,8,9}
        for vacancy in vacancies:
            (x,y,z) =             self.board.getElementInQuadrant(d1,d2,vacancy[0],vacancy[1])
            totalset = totalSet.intersection(set(z))
        if len(totalSet) == 1:
            return totalSet[0]           
        else:
            return 0
                
    def applyToColumn(self, i,j):
        vacancies  = self.board.getVacanciesInColumn(i,j)
        totalSet = {1,2,3,4,5,6,7,8,9}
        for vacancy in vacancies:
            (x,y,z) = self.board.getElement(vacancy[0],vacancy[1])
            totalset = totalSet.intersection(set(z))
        if len(totalSet) == 1:
            return totalSet[0]           
        else:
            return 0
                
    def applyToRow(self, i, j):
        vacancies  = self.board.getVacanciesInRow(i,j)
        totalSet = {1,2,3,4,5,6,7,8,9}
        for vacancy in vacancies:
            (x,y,z) = self.board.getElement(vacancy[0],vacancy[1])
            totalset = totalSet.intersection(set(z))
        if len(totalSet) == 1:
            return totalSet[0]           
        else:
            return 0
                 