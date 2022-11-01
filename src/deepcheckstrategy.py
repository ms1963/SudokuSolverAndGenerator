
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

    DeepCheckStrategy
    
this strategy takes all candidates
of (i,j) and analyzes whether it 
appears as influencer of all other
vacant cells. If yes, it is the 
number that should occupy (i,j)         
     
#############################################################
"""

######### DeepCheckStrategy ######### 
    
from board import Board, DIM, dim
from strategy import OccupationStrategy
        
    
class DeepCheckStrategy(OccupationStrategy): 
    def __init__(self, board):
        self.board = board
        
    def applyToQuadrant(self, i, j):
        (d1,d2,r,c) = self.board.inverseMapQuadrant(i,j)
        candidates  = self.board.getCandidates(i,j)
        vacancies   = self.board.getVacanciesInQuadrant(d1,d2,r,c)
        result = 0
        for num in candidates:
            counter = 0
            for vacancy in vacancies:
                row = vacancy[0]
                col = vacancy[1]
                (x,y,z) = self.board.getElementInQuadrant(d1, d2, row, col)
                if not num in z: break
                else: counter+=1
            if counter == len(vacancies): 
                result = num
                break
        return result
            
    def applyToColumn(self, i,j):
        candidates  = self.board.getCandidates(i,j)
        vacancies = self.board.getVacanciesInColumn(i,j)
        result = 0
        for num in candidates:
            counter = 0
            for vacancy in vacancies:
                row = vacancy[0]
                col = vacancy[1]
                (x,y,z) = self.board.getElement(row, col)
                if not num in z: break
                else: 
                    counter+=1
            if counter == len(vacancies): 
                result = num
                break
        return result
            
    def applyToRow(self, i, j):
        candidates  = self.board.getCandidates(i,j)
        vacancies = self.board.getVacanciesInRow(i,j)
        result = 0
        for num in candidates:
            counter = 0
            for vacancy in vacancies:
                row = vacancy[0]
                col = vacancy[1]
                (x,y,z) = self.board.getElement(row, col)
                if not num in z: break
                else: counter+=1
            if counter == len(vacancies): 
                result = num
                break
        return result
            