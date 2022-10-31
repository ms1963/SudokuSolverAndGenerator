"""
Distributed with:
GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
"""

######### Abstract Occupation Strategy base class #########   
# defines a trait all concrete strategies
# need to implement. applyStrategy is the only 
# method implemented in the base class respectively 
# trait Strategy
class OccupationStrategy:
    # constructor expects Board instance on which
    # the strategy instance is supposed to operate
    def __init__(self, board):
        pass
        
    # apply strategy to quadrant, row, and column
    # defined by (i,j). As soon as strategy returns
    # result != 0, we found a number that may occupy
    # (i,j). If 0 is returned, the strategy could 
    # not be applied
    # if necessary, concrete child classes may override
    # this method
    def applyStrategy(self, i, j):
        res = self.applyToQuadrant(i, j)
        if res != 0:
            return res
        res = self.applyToRow(i, j)
        if res != 0:
            return res
        res = self.applyToColumn(i, j)
        return res
                
    # abstract method: strategy applied to quadrant
    def applyToQuadrant(self, i, j):
        pass
    # abstract method: strategy applied to column
    def applyToColumn(self, i,j):
        pass
    # abstract method: strategy applied to row
    def applyToRow(self, i, j):
        pass
        
############# indirect influencers strategy class ############# 
# if there are one, two, or three vacant cells in a row/column 
# of a quadrant and the candidates for these cells accord to 
# the number of vacant cells, then we know that eventually 
# the vacant cells will be occupied by the candidates add 
# thus we know for certain that these candidates will become
# influencers for the rest of the board
    
    
############# Base class for all influence strategies ############ 
class InfluenceStrategy:
    def __init__(self, board):
        pass
    def applyStrategy(self):
        self.applyStrategyToRows()
        self.applystrategyToColumns()
        self.applyStrategyToQuadrants()