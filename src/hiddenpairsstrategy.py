############ HiddenPairsStrategy ############ 


from board import Board, DIM, dim
from strategy import InfluenceStrategy

class HiddenPairsStrategy(InfluenceStrategy):
    def __init__(self, board):
        self.board = board
    
    def applyStrategy(self):
        self.applyStrategyToQuadrants()
        self.applyStrategyToRows()
        self.applyStrategyToColumns()
        
    def handleHiddenPairs(self, cells, nums):
        assert len(cells) == DIM, "Error: array must have " + str(DIM) + " cells"
        cand = []
        occurrences = []
        n1,n2 = nums
        # go through all cells in the array
        for idx in range(0, DIM):
            # if the combination (n1,n2) is part of the cell
            i,j = cells[idx]
            cand = self.board.getCandidates(i,j)
            if (n1 in cand) and (n2 in cand):
                # append the cell to occurrences
                occurrences.append(cells[idx])
        # if the combination does not appear in exactly 2 cells
        if len(occurrences) != 2:
            return  # => return to caller
        else:
            # take both occurrences
            cell1 = occurrences[0]
            cell2 = occurrences[1]
            # get the candidate-list for these two cells
            c1i, c1j = cell1
            c2i, c2j = cell2
            cand1 = self.board.getCandidates(c1i, c1j)
            cand2 = self.board.getCandidates(c2i, c2j)
            # if lengths are greater than 2 we can continue
            if (len(cand1) > 2) and (len(cand2) > 2):
                # iterate through all possible numbers
                for num in range(1, DIM+1):
                    # if num is different from n1,n2
                    # it can be a candidate in the hidden pair
                    if (num != n1) and (num != n2):
                        
                        # => add it as an influencer
                        if not num in cand1:
                            self.board.addInfluencer(num, cell1[0], cell1[1])
                        if not num in cand2:
                            self.board.addInfluencer(num, cell2[0], cell2[1])
                           
    def applyStrategyToColumns(self):
        # iterate over all columns
        for j in range(1, DIM+1):
            array = []
            # get all rows and append (i,j) to array
            for i in range(1, DIM+1):
                array.append((i,j))
                # for all number combinations (n1,n2)
            for n1 in range(1, DIM):
                for n2 in range(n1+1, DIM+1):
                    # search for hidden pairs
                    self.handleHiddenPairs(array, (n1,n2))
                            
    def applyStrategyToRows(self):
        # iterate over all rows:
         for i in range(1, DIM+1):
            array = []
            # get all columns and append(i,j) to array
            for j in range(1, DIM+1):
                array.append((i,j))
            # for all number combinations (n1,n2)
            for n1 in range(1, DIM):
                for n2 in range(n1+1, DIM+1):
                    # search for hidden pairs
                    self.handleHiddenPairs(array, (n1,n2))
                    
    def applyStrategyToQuadrants(self):
        # for all quadrants (d1,d2):
        for d1 in range(1, dim+1):
            for d2 in range(1, dim+1):
                array = []
                # iterate through all cells in the quadrant
                for r in range(1, dim+1):
                    for c in range(1, dim+1):
                        # and append the cells to array
                        array.append(((d1-1) * dim + r, (d2-1) * dim + c))
                # check all number combinations (n1, n2)
                for n1 in range(1, DIM):
                    for n2 in range(n1+1, DIM+1):
                        # search for hidden pairs
                        self.handleHiddenPairs(array, (n1,n2))
                
            