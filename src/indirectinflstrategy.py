
"""    
    For rows or columns in a quadrant that have at least 1
    free cell such as in the following examples (dim = 3):
        
    ? ? ?     ? ? ?     ? o ?
    ? ? ?     o ? o     ? ? ?
    o o o     ? ? ?     ? ? ?
    
    where we know that in the known vacant cells (symbolized by o)
    the number of these cells equal the number of digits that can 
    occupy them, we know that these numbers influence the rest 
    of the extended row or column on the board.
    
    If for example, we got
    
    x x x
    o o o
    x x x
    
    and in the vacant cells the numbers 5, 8, 6 must be filled
    in, then these numbers will influence the extended row or
    column as well.
    
    If we do not know whether the ? above are occupied or free cells,
    we just build the union of potential digits that can be put in
    each known vacant cell. If the size of this union equals the 
    number of the vacant cells, then we extend the row/column 
    to the whole board.  
    
    """
############# Indirect Influencers Strategy ############ 
# This strategy may substiture other strategies such as 
# HiddenPairs, PointingPairsAndTriples, ....
            
from board import Board, DIM, dim
from strategy import InfluenceStrategy

class IndirectInfluencersStrategy(InfluenceStrategy):
    def __init__(self, board):
        self.board = board
    # check row of quadrant for indirect influencers      
    def analyzeRowInQuadrant(self,d1,d2, r):
        totalSet = set()
        countVacantCells = 0
        for c in range (1, dim+1):
            (x,y,z) = self.board.getElementInQuadrant(d1,d2,r,c)
            if x: continue # occupied cell
            else: 
                countVacantCells += 1
                candidates = self.board.calcCandidates(z)
                totalSet=totalSet.union(set(candidates))
        if len(totalSet) == countVacantCells:
            for num in totalSet:
                row = (d1-1)*dim + r
                for j in range(1,DIM+1):
                    (x,y,z) = self.board.getElement(row,j)
                    if not x and not (j in range((d2-1)*dim + 1, (d2-1)*dim + dim + 1)):
                        self.board.addInfluencer(num, row, j)
    
    # check column of quadrant for indirect influencers                    
    def analyzeColumnInQuadrant(self, d1, d2, c):
        totalSet = set()
        countVacantCells = 0
        for r in range (1, dim+1):
            (x,y,z) = self.board.getElementInQuadrant(d1,d2,r,c)
            if x: continue # occupied cell
            else: 
                countVacantCells += 1
                candidates = self.board.calcCandidates(z)
                totalSet=totalSet.union(set(candidates))
        if len(totalSet) == countVacantCells:
            for num in totalSet:
                col = (d2-1)*dim + c
                for i in range(1,DIM+1):
                    (x,y,z) = self.board.getElement(i, col)
                    if not x and not (i in range((d1-1)*dim + 1, (d1-1)*dim + dim + 1)):
                        self.board.addInfluencer(num, i, col)
      
    
    # iterates through all rows and columns of a quadrant
    def addIndirectInfluencersToQuadrant(self, d1,d2):
        for r in range(1,dim+1):
            self.analyzeRowInQuadrant(d1,d2,r)
        for c in range(1, dim+1):
            self.analyzeColumnInQuadrant(d1,d2,c)
    
    # iterates through all quadrants
    def applyStrategy(self):
        for d1 in range(1, dim+1):
            for d2 in range(1,dim+1):
                self.addIndirectInfluencersToQuadrant(d1,d2)