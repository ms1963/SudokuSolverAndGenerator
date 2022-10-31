######### RemainingInfluencerStrategy #########           
# this strategy searches for other vacant cells 
# and checks whether there is an influencer that 
# appears in all of these vacant cells. Since 
# the number can not be a candidate in all 
# other vacant cells, it must be the number that 
# should be put into (i,j)

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
                 