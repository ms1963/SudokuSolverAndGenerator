############ OneCandidateLeftStrategy ############ 
# this strategy analyzes whether there is only
# one candidate left for (i,j). If yes, this 
# must be the right number to fill IndentationError

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
            