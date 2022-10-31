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
This package consist of the core classes:

    SudokuSolver 
        and 
    Strategies
    
    
    
SudokuSolver helps solving Sudoku puzzles. 
            
#############################################################
"""

# dependencies:
import   csv
import   time
from     enum    import Enum, unique
from     random  import shuffle
from     copy    import copy, deepcopy
import   os.path
from     memory  import StatePersistence
from     chains  import Chain
from     generator import SudokuGenerator
from     strategy import OccupationStrategy, InfluenceStrategy
from     board   import Board, DIM, dim




"""
WARNING: this code is not tested with dim other than 3. 
It might mot even work. In addition, some strategies do 
only apply to dim == 3
"""

dim = 3          # size of Sudoku quadrants
DIM = dim * dim  # size of Sudoku puzzle

# make sure that dim and DIM have valid values
assert isinstance(dim, int), 'dim must be an integer'
assert isinstance(DIM, int), 'DIM must be an integer'
assert dim > 0, 'dim must be positive'
assert DIM > 0, 'DIM must be positive'
assert dim * dim == DIM, 'DIM must be dim * dim'

 
# specifies constants with unique values that determine
# display mode of displayXXX()-methods.

@unique   
class Info(Enum):     
        NONE           = 0 # no output
        ALL            = 1 # all information is written to the console
        INFLUENCERS    = 2 # list of influencers for all cells
        OCCUPANTS      = 3 # list of occupants
        CANDIDATES     = 4 # list of candidates 
        PRETTY         = 5 # pretty print of board 
        
# coordinates in SudokuSolver as seen by the caller
# DIM = 9 (dim = 3)
# x in 1..9 
# y in 1..9 
#
# quadrants:
#
# Quadrant 1,1:
# d1 in 1..3 
# d2 in 1..3 
# Quadrant 1,2:
# d1 in 1..3 
# d2 in 4..6     
#
# internally these user coordinates are mapped to 
# an internal index to an one-dimensional array _data[]
    
# The Solver class. 
# If a solver is instantiated with 
# withCheating == True, 
# the solver will look up 
# cells in a brute force solution whenever it fails
# to find the occupant of a cell using another
# strategy
# If a solver is instantiated with 
# withMonitoring == True, 
# it will display more information about what is
# going on under the hood. This is useful for 
# analysis of  internal behavior.

class SudokuSolver:
    # self._data is an one-dimensional array that
    # stores all information for the Sudoku board. 
    # It consists of tuples (x, y, z)
    # x = True => position occupied by number y 
    # x = False=> position influenced by other numbers 
    #             defined in z without being occupied
    
    
    # call self.reinitialize() to delete _data[] and
    # initialize it with new values
    # and register required (predefined) strategies
    def __init__(self, withCheating, withMonitoring):
        self.board = None
        # withCheating == True => SudokuSolver uses Cheating:
        self.withCheating = withCheating 
        # obtaining messages about what is going on
        # internally:
        self.monitoringActive = withMonitoring
        self.reinitialize() # prepare board
        self.occupationStrategies = [] # init strategies
        self.influenceStrategies = []
        
        
        ## add strategies ## 
        
        # occupation strategies:
        
        strategy = self.DeepCheckStrategy(self.board)
        self.attachOccupationStrategy(strategy)
        strategy = self.OneCandidateLeftStrategy(self.board)
        self.attachOccupationStrategy(strategy)
        strategy = self.RemainingInfluencerStrategy(self.board)
        self.attachOccupationStrategy(strategy)
       
        if self.withCheating:
            strategy = self.Cheating(self.board)
            self.attachOccupationStrategy(strategy)
        
        # influence strategies
        strategy = self.XWingStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        strategy = self.SwordFishStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        strategy = self.HiddenPairsStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        strategy = self.HiddenTriplesStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        strategy = PointingPairsAndTriplesStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        strategy = self.IndirectInfluencersStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        
    # deletes and reinitializes self._data
    # Note: registered strategies are left untouched
    def reinitialize(self):
        self.states = {}
        data = [(False,0,[]) for i in range(0, DIM*DIM)]
        self.board = Board(data)
        if self.monitoringActive:
            self.board.turnMonitoringOn()
        else:
            self.board.turnMonitoringOff()

    def getInstalledInfluenceStrategies(self):
        strategyList = []
        for strategy in self.influenceStrategies:
            strategyList.append(strategy)
        return strategyList
            
    def getInstalledOccupationStrategies(self):
        strategyList = []
        for strategy in self.occupationStrategies:
            strategyList.append(strategy)   
        return strategyList
            
    # registration method to attach occupation strategies. 
    # Strategies can be  added in __init()__ or externally 
    # by the user of the class    
    def attachOccupationStrategy(self, strategy):
        self.occupationStrategies.append(strategy)
            
    # registration method to attach influence strategies. 
    # Strategies can be  added in __init()__ or externally 
    # by the user of the class    
    def attachInfluenceStrategy(self, strategy):
        self.influenceStrategies.append(strategy)
        
        
    
                
    ######### RemainingInfluencerStrategy #########           
    # this strategy searches for other vacant cells 
    # and checks whether there is an influencer that 
    # appears in all of these vacant cells. Since 
    # the number can not be a candidate in all 
    # other vacant cells, it must be the number that 
    # should be put into (i,j)
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
                 
    ######### DeepCheckStrategy ######### 
    # this strategy takes all candidates
    # of (i,j) and analyzes whether it 
    # appears as influencer of all other
    # vacant cells. If yes, it is the 
    # number that should occupy (i,j)          
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
            
    ############ OneCandidateLeftStrategy ############ 
    # this strategy analyzes whether there is only
    # one candidate left for (i,j). If yes, this 
    # must be the right number to fill in
    
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
            if len(z) == DIM-1: # exactly one number is missing 
                              # in the influencer list which 
                              # needs to be the one to be put 
                              # in (i,j)
                # thus candidates has only one entry
                candidates = self.board.getCandidates(i,j)
                # the only candidate left is returned 
                return candidates[0] # return that number
            return result
            
    
    ############ Cheating ############ 
    # this strategy just searches whether a given
    # cell is unoccupied. If that is the case it 
    # looks up the number in a brute force solution
    
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
    

    # method to build all permutations of a list 
    def permutations(self, list):
        if len(list) == 0:
            return []
        elif len(list) == 1:
            return [list]
        else:
            resultList = [] 
            for idx in range(len(list)):
               first = list[idx]
               rest = list[:idx] + list[idx+1:]
           
               for perm in permutations(rest):
                   resultList.append([first] + perm)
               
            return resultList


    
    ############# occupation related methods ############
        
    # which number must be placed in this location?
    # Returns 0 if no number can be placed since location  
    # is already occupied or more than one number is possible
                    
    def canBeOccupied(self, i, j):
        retVal = (0, "")
        (x, y, z) = self.board.getElement(i,j) # get entry
        if not x:
            for strategy in self.occupationStrategies:
                result = strategy.applyStrategy(i,j)
                if result != 0: 
                    retVal = (result, type(strategy).__name__)
                    break
        return retVal
                   
    # occupy field with number
    # set surpress to True to prevent information abour
    # called InfluenceStrategies
    def occupy(self, number, i, j):
        # get internal data for (i,j)
        (x, y, z) = self.board.getElement(i,j)
        # check if (i,j) is already occupied
        # this also ensures that no occupation
        # strategy gets an occupied cell passed
        if x: # is (i,j) already occupied
            print("Error: Position ("+str(i)+"," + str(j) + ") " + "already occupied by " + str(y))
            return
        else: # cell is vacant
            (x_old, y_old, z_old) = (x, y, z) # save previous content
            x = True  # mark cell as occupied
            y = number # set number which occupies the cell
            z = [] # clear influencers
            self.board.setElement(i,j, (x,y,z)) # update _data[]
            if not self.board.checkConformanceOfBoard(): # check for conformance
                print("Error: rule violation in (" + str(i) + "," + str(j) + ") when entering " + str(number))
                print("Restoring previous content")
                (x, y, z) = (x_old, y_old, z_old)
                self.board.setElement(i,j,(x,y,z))
            else:
                # reanalyze the board, as some influencers have been 
                # introduced by occupying (i,j), so that the occupation
                # strategies work
                if self.monitoringActive:
                        print("Adding influencers to board after occupying (" + str(i) + "," + str(j) + ")")
                self.board.addInfluencerToRegionExclusive(number, i, j)
                # call all strategies which may remove candidates
                # from some cells which is equivalent to adding
                # influencers
                for strategy in self.influenceStrategies:
                    if self.monitoringActive:
                        print("Applying strategy " + type(strategy).__name__)
                    strategy.applyStrategy()
    
    # is position occupied. Other method would be 
    # to check for not ((i,j) in vacancies)        
    def isOccupied(self, i, j):
        (x, y, z) = self.board.getElement(i,j)
        return x        

        
    
        
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
                    
                    

    ################## X-Wing  Strategy ####################### 
    # This strategy identifies two rows (or two columns) where
    # there are only two cells left which can be occupied with
    # a number called pivot. If these cells are also aligned
    # with respect to their columns (or rows) and build a 
    # rectangular formation, a so-called X-Wing, then we know
    # that in the two columns (or rows) we can remove the pivot
    # as a candidate from the aforementioned columns (or rows)
    
    class XWingStrategy(InfluenceStrategy):
        def __init__(self, board):
            self.board = board
            
        # find all cells in row r which contain the pivot element
        def findCandidatesInRow(self,pivot, r):
            listOfCellsInARow = []
            for c in range(1, DIM+1): # check all columns 
                (x,y,z) = self.board.getElement(r,c)
                if not x: # vacant cell
                    if not pivot in z: # <=> pivot in candidates
                        listOfCellsInARow.append((r, c))
            return listOfCellsInARow

        # find all cells in column c which contain the pivot element
        def findCandidatesInColumn(self,pivot, c):
            listOfCellsInAColumn = []
            for r in range(1, DIM+1): # check all rows
                (x,y,z) = self.board.getElement(r,c)
                if not x: # vacant cell
                    if not pivot in z: # <=> pivot in candidates
                        listOfCellsInAColumn.append((r, c))
            return listOfCellsInAColumn

        # find X-Wings defined by rows
        def applyStrategyToRows(self):
            numbers = [n for n in range(1, DIM+1)]
            for pivot in numbers: # search for all possible numbers as pivots
                listOfCellsInARow = []
                listOfRows = []
                for r in range(1, DIM+1): # iterate through all rows r
                    # get all cells in r which contain pivot
                    listOfCellsInARow = self.findCandidatesInRow(pivot, r)
                    # if there are only two cells in r that have pivot 
                    # as a candidate
                    # we found a candidate row
                    if len(listOfCellsInARow) == 2: # we need rows with 2 cells
                        listOfRows.append(listOfCellsInARow)
                # only if there are at least two 
                # candidate rows we can search for possible 
                # X-Wing formations
                if len(listOfRows) >= 2:
                    xWingList = self.searchForXWingRows(listOfRows)
                    for xWing in xWingList: # iterate through all 
                                            # XWings found which are diagonals
                        (r11,c11,r22,c22) = xWing # diagonal with (r11,c11) as
                                     # upper left and (r22,c22) as lower right
                        exceptionList= [r11, r22] # rows not to add influencer
		
                        # add Influencer == pivot to column c11
                        self.board.addInfluencerToColumn(pivot, c11, exceptionList)
                        # add Influencer == pivot to column c22
                        self.board.addInfluencerToColumn(pivot, c22, exceptionList)

        # # find X-Wings defined by columns        
        def applyStrategyToColumns(self):
            numbers = [n for n in range(1, DIM+1)]
            for pivot in numbers: # search for all possible numbers as pivots
                listOfCellsInAColumn = []
                listOfColumns = []
                for c in range(1, DIM+1): # iterate through all rows c
                    # get all cells in r which contain pivot
                    listOfCellsInAColumn = self.findCandidatesInColumn(pivot, c)
                    # if there are only two cells in c that 
                    # have pivot as a candidate
                    # we found a candidate row
                    if len(listOfCellsInAColumn) == 2: # we need columns 
                                                        # with 2 cells
                        listOfColumns.append(listOfCellsInAColumn)
                # only if there are at least 2 candidate rows we can search 
                # for possible X-Wing formations
                if len(listOfColumns) >= 2:
                    xWingList = self.searchForXWingColumns(listOfColumns)
                    for xWing in xWingList: # iterate through all XWings  
                                            # which are diagonals
                        
                        (r11,c11,r22,c22) = xWing 
                        exceptionList= [c11, c22] # rows not to add influencer
		
                        # add Influencer == pivot to column c11
                        self.board.addInfluencerToRow(pivot, r11, exceptionList)
                        # add Influencer == pivot to column c22
                        self.board.addInfluencerToRow(pivot, r22, exceptionList)

        # listOfColumns contains all columns with only two cells 
        # where pivot is a candidate
        def searchForXWingColumns(self, listOfColumns):
            xWings = []
            # iterate through all columns with two pivot cells
            for k in range(0, len(listOfColumns)-1):
                for l in range(k+1, len(listOfColumns)): # take 2 columns
                    col1Pair = listOfColumns[k]
                    col2Pair  = listOfColumns[l]
                    xWing  =  self.getXWingColumn(col1Pair, col2Pair)
                    if xWing != None: # if we got two columns with 
                                        # cells aligned in the same rows
                        xWings.append(xWing) # add the XWing to the result
            return xWings

        # listOfRows contains all columns with only two cells where 
        # pivot is a candidate
        def searchForXWingRows(self, listOfRows):
            xWings = []
            # iterate through all rows with two pivot cells
            for k in range(0, len(listOfRows)-1):
                for l in range(k+1, len(listOfRows)): # take two of the rows
                    row1Pair  = listOfRows[k]
                    row2Pair  = listOfRows[l]
                    xWing  =  self.getXWingRow(row1Pair, row2Pair)
                    if xWing != None:   # if we got 2 rows with cells aligned 
                                        # in the same columns
                        xWings.append(xWing) # add the XWing to the result
            return xWings

        # if the cells are aligned in same columns, we got an X-Wing formation
        def getXWingRow(self, rowAPair, rowBPair):
            ((r11,c11),(r12,c12)) = rowAPair
            ((r21,c21),(r22,c22)) = rowBPair
            if (c11 == c21) and (c12 == c22):
                return (r11, c11, r22, c22)
            else:
                return None

        # if the cells are aligned in same rows, we got an X-Wing formation
        def getXWingColumn(self, colAPair, colBPair):
            ((r11,c11),(r12,c12)) = colAPair
            ((r21,c21),(r22,c22)) = colBPair
            if (r11 == r21) and (r12 == r22):
                return (r11, c11, r22, c22)
            else:
                return None
                
        # apply strategy to columns and rows
        def applyStrategy(self):
            self.applyStrategyToColumns()
            self.applyStrategyToRows()
            
    
	############ Swordfish Strategy ################

    class SwordFishStrategy(InfluenceStrategy):
        def __init__(self, board):
            self.board = board
        
        # check how often the pivot appears in the row
        def rowContainsCandidate(self, pivot, r):
            result = 0
            # search in all columns
            for c in range(1, DIM+1):
                (x,y,z) = self.board.getElement(r,c)
                if x: continue # continue when occupied
                if pivot in self.board.getCandidates(r,c):
                    result += 1
            return result

        # check how often the pivot appears in the column
        def columnContainsCandidate(self, pivot, c):
            # search in all rows
            for r in range(1, DIM+1):
                result = 0
                (x,y,z) = self.board.getElement(r,c)
                if x: continue # continue when occupied
                if pivot in self.board.getCandidates(r,c):
                    result += 1
            return result

        # checks for the three columns specified 
        # in which rows the pivot can be found
        def matchingRows(self, pivot, c1, c2, c3):
            rowList = []
            # search in all rows where pivot is a candidate 
            for r in range(1,DIM+1):
                if (pivot in self.board.getCandidates(r, c1)) or (pivot in self.board.getCandidates(r, c2)) or (pivot in self.board.getCandidates(r, c3)):
                    rowList.append(r)
            return rowList

        # checks for the three rows specified 
        # in which columns the pivot can be found
        def matchingColumns(self, pivot, r1, r2, r3):
            colList = []
            # search in all columns where pivot is a candidate 
            for c in range(1,DIM+1):
                if (pivot in self.board.getCandidates(r1, c)) or (pivot in self.board.getCandidates(r2, c)) or (pivot in self.board.getCandidates(r3, c)):
                    colList.append(c)
            return colList

        # for all pivots and all configurations of 3 columns where
        # the pivot is found 2 or 3 times as a candidate, it is checked
        # whether there are only three rows in which the pivot is a 
        # candidate. If yes, SwordFisgh can be applied by removing
        # the candidates from these rows which are not in one of 
        # the columns
        def applyStrategyToColumns(self):
            for pivot in range(1, DIM+1):
                for c1 in range(1, DIM-1):
                    howMany = self.columnContainsCandidate(pivot, c1)
                    if howMany <= 1 or howMany > dim: continue
                    for c2 in range(c1+1, DIM):
                        howMany = self.columnContainsCandidate(pivot, c2)
                        if howMany <= 1 or howMany > dim: continue
                        for c3 in range(c2+1, DIM+1):
                            howMany = self.columnContainsCandidate(pivot, c3)
                            if howMany <= 1 or howMany > dim: continue
                            rowList = self.matchingRows(pivot,c1,c2,c3)
                            if len(rowList) == dim:
                                for r in rowList:
                                    self.board.addInfluencerToRow(pivot, r, [c1, c2, c3])

        # for all pivots and all configurations of 3 rows where
        # the pivot is found 2 or 3 times as a candidate, it is checked
        # whether there are only three columns in which the pivot is a 
        # candidate. If yes, SwordFisgh can be applied by removing
        # the candidates from these columns which are not in one of 
        # the rows
        def applyStrategyToRows(self):
            for pivot in range(1, DIM+1):
                for r1 in range(1, DIM-1):
                    howMany = self.rowContainsCandidate(pivot, r1)
                    if howMany <= 1 or howMany > dim: continue
                    for r2 in range(r1+1, DIM):
                        howMany = self.rowContainsCandidate(pivot, r2)
                        if howMany <= 1 or howMany > dim: continue
                        for r3 in range(r2+1, DIM+1):
                            howMany = self.rowContainsCandidate(pivot, r3)
                            if howMany <= 1 or howMany > dim: continue
                            colList = self.matchingColumns(pivot,r1,r2,r3)
                            if len(colList) == dim:
                                for c in colList:
                                    self.board.addInfluencerToColumn(pivot, c, [r1, r2, r3])

        def applyStrategy(self):
            self.applyStrategyToColumns()
            self.applyStrategyToRows()
            
    ############ HiddenPairsStrategy ############ 
    
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
                    
                
 ############ HiddenTriples Strategy ############ 
    
    class HiddenTriplesStrategy(InfluenceStrategy):
        def __init__(self, board):
            self.board = board
        
        def applyStrategy(self):
            self.applyStrategyToQuadrants()
            self.applyStrategyToRows()
            self.applyStrategyToColumns()
            
        def handleHiddenTriples(self, cells, nums):
            assert len(cells) == DIM, "Error: array must have " + str(DIM) + " cells"
            cand = []
            occurrences = []
            n1,n2,n3 = nums
            # go through all cells in the array
            for idx in range(0, DIM):
                # if the combination (n1,n2) is part of the cell
                i,j = cells[idx]
                cand = self.board.getCandidates(i,j)
                if (n1 in cand) and (n2 in cand) and (n3 in cand):
                    # append the cell to occurrences
                    occurrences.append(cells[idx])
            # if the combination does not appear in exactly 2 cells
            if len(occurrences) != 3:
                return  # => return to caller
            else:
                # take the 3 occurrences
                cell1 = occurrences[0]
                cell2 = occurrences[1]
                cell3 = occurrences[2]
                # get the candidate-list for these two cells
                c1i, c1j = cell1
                c2i, c2j = cell2
                c3i, c3j = cell3
                cand1 = self.board.getCandidates(c1i, c1j)
                cand2 = self.board.getCandidates(c2i, c2j)
                cand3 = self.board.getCandidates(c3i, c3j)
                # if lengths are greater than 2 we can continue
                if (len(cand1) > 3) and (len(cand2) > 3) and (len(cand3) > 3):
                    # iterate through all possible numbers
                    for num in range(1, DIM+1):
                        # if num is different from n1,n2
                        # it can be a candidate in the hidden pair
                        if (num != n1) and (num != n2) and (num != n3):
                            # => add it as an influencer
                            if not num in cand1:
                                self.board.addInfluencer(num, c1i, c1j)
                            if not num in cand2:
                                self.board.addInfluencer(num, c2i, c2j)
                            if not num in cand3:
                                self.board.addInfluencer(num, c3i, c3j)
                               
        def applyStrategyToColumns(self):
            # iterate over all columns
            for j in range(1, DIM+1):
                array = []
                # get all rows and append (i,j) to array
                for i in range(1, DIM+1):
                    array.append((i,j))
                    # for all number combinations (n1,n2)
                for n1 in range(1, DIM-1):
                    for n2 in range(n1+1, DIM):
                        for n3 in range(n2+1, DIM+1):
                            # search for hidden triples
                            self.handleHiddenTriples(array, (n1,n2,n3))
                                
        def applyStrategyToRows(self):
            # iterate over all rows:
             for i in range(1, DIM+1):
                array = []
                # get all columns and append(i,j) to array
                for j in range(1, DIM+1):
                    array.append((i,j))
                # for all number combinations (n1,n2)
                for n1 in range(1, DIM-1):
                    for n2 in range(n1+1, DIM):
                        for n3 in range(n2+1, DIM+1):
                            # search for hidden pairs
                            self.handleHiddenTriples(array, (n1,n2,n3))
                        
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
                    for n1 in range(1, DIM-1):
                        for n2 in range(n1+1, DIM):
                            for n3 in range(n2+1, DIM+1):
                                # search for hidden triples
                                self.handleHiddenTriples(array, (n1,n2,n3))   
       
    ############## reading in board from other formats ##############
    # check string list for well-formating
    def checkString(self, sl):
        if len(sl) != DIM * DIM:
            print("Error: wrong length of list: " + str(len(sl)))
            return False
     
        for idx in range(0, DIM*DIM):
            if sl[idx] in ['0','1','2','3','4','5','6','7','8','9']:
                continue      
            else:
                print("Error: invalid char " + sl[idx] + " at " + str(i))
                return False
        return True 
    
    # prepare a string list of a Sudoku and let 
    # it be converted to internal board _data[]
    def turnStringIntoBoard(self, sl):
        sl = sl.replace(" ","") # removing blanks
        assert(self.checkString(sl))
        for idx in range(0, DIM*DIM):
            val = int(sl[idx])
            if val != 0:
                self.occupy(val, idx // DIM + 1,  idx % DIM + 1)
        self.vacancies = self.board.getVacancies()
        
    # take a one-dimensional list and convert it to Sudoku board 
    # but only if board conforms to Sudoku rules
    def turnListIntoBoard(self, rows):
        _data = deepcopy(self.board._data)
        for i in range(0, DIM*DIM):
            num = rows[i]
            if num != 0:
                self.occupy(num, i // DIM + 1, i % DIM + 1)
        if not self.board.checkConformanceOfBoard(): # if invalid board
            self.board = Board(_data)
        self.vacancies = self.board.getVacancies()
    ############# display methods ############# 
             
    # display whole board 
    # Info.ALL  => print all data 
    # Info.INFLUENCERS => print influencers 
    # Info.OCCUPANTS => print occupants       
        
    def displayBoard(self, info = Info.ALL, compact = False):
        if info == Info.NONE: return
        for k in range(1,DIM+1):
            if (info == Info.OCCUPANTS) and (k > 1) and ((k - 1) % 3 == 0): 
                print("----------------------------------------")
                print()
            for l in range(1,DIM+1):
                if (info == Info.OCCUPANTS) and (l > 1) and ((l - 1) % 3 == 0): 
                    print("|", end = " ")
                (x,y,z) = self.getElement(k,l)
                if x:
                    if info == Info.ALL:
                        print("[" + str(k) + "," +str(l) + "] y = *" +str(y), end = " ")
                    elif info == Info.INFLUENCERS:
                        if not compact:
                            print("[" + str(k) + ":" +str(l) + "] =", end = " ")
                        print("(" + str(y) + "*)", end = " ")
                    elif info == Info.CANDIDATES:
                        if not compact:
                            print("[" + str(k) + ":" +str(l) + "] =", end = " ")
                        print("(" + str(y) + " *)", end = " ")
                    else:
                        print(" " + str(y) + " ",end = " ")
                else:
                    if info == Info.ALL:
                        print("[" + str(k) + "," +str(l) + "] z = " + str(z), end = " " )
                        print(x,y,z);
                    elif info == Info.INFLUENCERS:
                        if not compact:
                            print("[" + str(k) + ":" +str(l) + "] =", end = " ")
                        print(z, end = " ")
                    elif info == Info.CANDIDATES:
                        if not compact: 
                            print("[" + str(k) + ":" +str(l) + "] =", end = " ")
                        print(self.calcCandidates(z), end = " ")
                    else:
                        print("   ",end= " ")
            print()
            print()
            
    # display just the quadrant
    def displayQuadrant(self, d1, d2, info = Info.ALL):
        if info == Info.NONE: return
        for k in range(1,dim+1):
            for l in range(1,dim+1):
                (x,y,z) = self.getElementInQuadrant_data(d1,d2,k,l)
                if x:
                    if info == Info.ALL:
                        print("(" + str(k) + "," +str(l) + ")")
                        print(x,y,z)
                    elif (info == Info.INFLUENCERS) or (info == Info.CANDIDATES):
                        print("(" + str(y) + " *)", end = " ")
                    else:
                        print(y,end = " ")
                else:
                    if info == Info.ALL:
                        print(x,y,z);
                    elif info == Info.INFLUENCERS:
                        print(z, end = " ")
                    elif info == Info.CANDIDATES:
                        print(self.calcCandidates(z), end = " ")
                    else:
                        print(0,end= " ")
            print()
            
    # display a row
    def displayRow(self, row, info = Info.ALL):
        if info == Info.NONE: return
        for c in range(1,DIM+1):
            (x,y,z) = self.getElement(row, c)
            if x:
                if info == Info.ALL:
                    print("(" + str(row) + "," +str(c) + ")")
                    print(x,y,z)
                elif (info == Info.INFLUENCERS) or (info == Info.CANDIDATES):
                    print("(" + str(y) + " *)", end = " ")
                else:
                    print(y,end = " ")
            else:
                if info == Info.ALL:
                    print("(" + str(row) + "," +str(c) + ")")
                    print(x,y,z);
                elif info == Info.INFLUENCERS:
                    print(z, end = " ")
                elif info == Info.CANDIDATES:
                    print(self.calcCandidates(z), end = " ")
                else:
                    print(0,end= " ")
        print()
    
    # display a column        
    def displayColumn(self, col, info = Info.ALL):
        if info == Info.NONE: return
        for r in range(1,DIM+1):
            (x,y,z) = self.getElement(r, col)
            if x:
                if info == Info.ALL:
                    print("(" + str(r) + "," +str(col) + ")")
                    print(x,y,z)
                elif (info == Info.INFLUENCERS) or (info == Info.CANDIDATES):
                    print("(" + str(y) + " *)")
                else:
                    print(y)
            else:
                if info == Info.ALL:
                    print("(" + str(r) + "," +str(col) + ")")
                    print(x,y,z);
                elif info == Info.INFLUENCERS:
                    print(z)
                elif info == Info.CANDIDATES:
                    print(self.calcCandidates(z))
                else:
                    print(0)
        print()
        
    ############# prettyPrint methods ############## 
    
    # using convertToIntArray _data[] is converted
    # to a two dimensional array of ints.
    # this array can be printed using prettyPrint()
    def convertToIntArray(self):
        intarray = []
        for i in range(1, DIM+1):
            row = []
            for j in range(1, DIM+1):
                row.append(self.board.getOccupant(i,j))
            # add row to intarray
            intarray.append(row)
        return intarray
        
    # prettyPrint displays the Sudoku board in a textual
    # but nice way
    def prettyPrint(self, board):
        def createLine(row):
            return row[0]+row[5:9].join([row[1:5]*(dim-1)]*dim)+row[9:13]
        
        symbol = " 1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        nums   = [ [""]+[symbol[n] for n in row] for row in board ]

        line0  = createLine("╔═══╤═══╦═══╗")
        line1  = createLine("║ . │ . ║ . ║")
        line2  = createLine("╟───┼───╫───╢")
        line3  = createLine("╠═══╪═══╬═══╣")
        line4  = createLine("╚═══╧═══╩═══╝")

        print(line0)
        for r in range(1,DIM+1):
            print( "".join(n+s for n,s in zip(nums[r-1],line1.split("."))) )
            print([line2,line3,line4][(r % DIM==0)+(r % dim==0)])
    
    # method to print board with candidates or influencers perspective
    # it uses the method getElement(i,j) zo access individual cells:        
    def printCandidatesAndInfluencers(self, candidates = True, title = ""):
        assert dim == 3, "sudokuPrint only supports standard Sudoku puzzles"

        # filledStrings returns a formatted string with a maximum
        # of three candidates or influencers
        def filledString(lst, requiredSize = 3):
            if requiredSize < len(lst):
                raise ValueError("requiredSize must be greater or equal to length of list")
            result = " "
            # print elements of lst 
            for elem in lst:
                result += str(elem) + " "
            # if we need to fill up missing numbers, 
            # then we are filling the gaps:
            delta = requiredSize - len(lst)
            if delta > 0:
                for idx in range(0, delta): 
                    result += "  "
            result += " "
            return result
    
        # numberStrings returns formatted strings if the cell is 
        # occupied by a number (occupant or single influencer/candidate)
        def numberStrings(number, isOccupant = True):
            lines = []
            lines.append("        ")
            if isOccupant:
                lines.append("  *" + str(number) + "*   ")
            else:
                lines.append("   " + str(number) + "    ")
            lines.append("        ")
            return lines
        
        
        # body of printCandidatesAndInfluencers():
    
        if title != "": 
            print("                               " + title)
        print("----------------------------------------------------------------------------------")
        for r in range(1, DIM+1):
            line1 = "| " 
            line2 = "| "
            line3 = "| "
            for c in range(1, DIM+1):
                cell = []
                number = 0
                # get Element at (r,c)
                (x,y,z) = self.board.getElement(r,c)
                if not x: # unoccupied cell
                    # the unoccupied cell is instantiated with 
                    # candidates (if candidates == True) or 
                    # with influencers
                    if not candidates: # influencers are needed
                        cell = z
                    else:  # candidates are needed
                        cell = self.board.calcCandidates(z)
                    size = len(cell) # measure length of cell
                else: # occupied cell
                    number = y # get occupant
                
                if not x: # cell is not occupied
                    if size <= 3: 
                        line1 += filledString([])
                        line2 += filledString(cell[0:3])
                        line3 += filledString([])
                    else:
                        line1 += filledString(cell[0:3])
                        line2 += filledString(cell[3:6])
                        line3 += filledString(cell[6:])
                        
                else: # we are dealing with an occupied cell
                    lines = numberStrings(number, isOccupant = True)
                    line1 += lines[0]
                    line2 += lines[1]
                    line3 += lines[2]
                if c % 3 == 0: # draw border of current quadrant
                    line1 += " | "
                    line2 += " | "
                    line3 += " | "
   
            print(line1)
            print(line2)
            print(line3)
            # print border of current row
            if r % 3 == 0:
                print("----------------------------------------------------------------------------------")
                # print()
            else:
                print()
        print("Legend: '* number *' specifies the occupant of a cell.")
        print()
        print("        ' 1 2 3 '")
        print("        ' 4 5 6 '    specify the influencers or canadidates.")
        print("        ' 7     '")
            
    
    ############# solver methods ############# 

    # checks whether all cells are occupied 
    # can also checked with vacancies == [] instead
    def isCompleted(self):
        for idx in range(0, DIM*DIM):
            (x,y,z) = self.board._data[idx]
            if not x:
                return False
        return True
    
    bfs = "" # used to cache results of solveBF()-invocations 
                
    # make sure that cells contain '0', '1', ... , 'DIM'
    def wellFormed(self, string):
        for idx in range(0, DIM*DIM):
            if string[idx] in {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}:   
                continue
            else:
                return False
        return True           
                
    # Brute Force Algorithm
    # solveBF gets a one-dimensional string as input (with the 
    # digits "0".."9" as characters). "0" represents an empty
    # cell. The actual work is done in solveBruteForce().
    # It returns the result of the brute force calculation to 
    # the caller
    def solveBF(self, string):
        def solveBruteForce(string):
            # all numbers in same row, column or quadrant define
            # numbers that can not be in a cell. influencer determines
            # if content at index i and index j influence each
            # other
            def influencer(i,j):
                return (i//DIM == j//DIM) or (i%DIM == j%DIM) or  (((i//DIM)//dim == (j//DIM)//dim) and ((i%DIM)//dim == (j%DIM)//dim))
        
            # find the first vacant cell. Vacant cells contain '0'
            vacancy = string.find('0')
        
            # which numbers are not allowed because of other
            # cells in the neighborhood
            influencers = {string[j] for j in range(len(string)) if influencer(vacancy, j)}
            # all possible digits ("1", "2", ...., DIM):
            all = {str(num) for num in range(1, DIM+1)}
            
            # subtract the numbers that can't occupy the cell
            candidates = all - influencers

            # iterate through all candidates
            for num in candidates:
                # build a new string with the analyzed cell occupied
                # by num 
                string = string[0:vacancy] + num + string[vacancy+1:]
                # and call solveBruteForce with the modified 
                # string recursively
                solveBruteForce(string) # ignore results
                # if the resulting string comprises no vacant cells,  
                # we are done
                if string.find('0') == -1:
                    self.bfs = string # store result in bfs
        
        if len(string) != DIM*DIM:
            print("Error length is not " + str(DIM*DIM))
            return ""
        if not self.wellFormed(string):
            print("Error: string contains invalid characters")
            return ""
       
        solveBruteForce(string) # delegate to solveBruteForce()
        return self.bfs # return result to caller
        # bfs stands for brute force solution
                
    # while Sudoku is not solved,
    # loop through all cells of the board 
    # and find all cells that can be occupied.
    # If cell can be occupied, put number into cell.
    # If no cells could be occupied, the strategies
    # used for solving the Sudoku are insufficient 
    # and the loop stops with an error message.
    # Returns True on success and False on failure
    # info as argument specifies if and how the 
    # board should be displayed
    def solve(self, info = Info.PRETTY):
        if not self.board.checkConformanceOfBoard(): # board must conform to rules
            print ("Error: board does not conform to Sudoku rules")
            return
        self.steps = 0
        if self.withCheating:
            boardAsString = self.board.turnBoardIntoString()
            solution = self.solveBF(boardAsString)
            self.board.storeBFSolution(solution)
        if info == Info.PRETTY:
            self.prettyPrint(self.convertToIntArray())
        else: 
            self.displayBoard(info) # show initial board 
        while not self.isCompleted(): # while not all cells are occupied
            changes = 0
            for i in range(1, DIM+1):       # iterate through all board
                for j in range(1, DIM+1):   # cells and find a cell that 
                                            # can be occupied.
                    (n, msg) = self.canBeOccupied(i, j)
                    if n != 0: # if cell can be occupied 
                        print("[" + str(i) + "," + str(j) + "] <- " + str(n))
                        if self.monitoringActive:
                            print("Strategy used = " + msg)                     
                        if info != Info.NONE:   
                            print("(SudokuSolver): Enter <any key> to continue, q to quit, <cmd> for another command, h to display help about commands")
                            value = input(" ---> ")
                            print()
                            match value:
                                case "q": 
                                    print("Exiting from SudokuSolver ...")
                                    return True # True because user aborts
                                case "b":
                                    print("Saving state to Persistence")
                                    while True:
                                        name = input(" Specify name ---> ")
                                        if name != "" and not name in StatePersistence().keys():
                                            StatePersistence().persistState(name, self.board._data)
                                            break
                                case "w":
                                    rows = self.board.turnBoardIntoList()
                                    while True:
                                        fname = input("* Enter name of output file: ")   
                                        if os.path.isfile(fname):
                                            print("  Error - file already exists. Use another filename.")
                                        elif len(fname) == 0:
                                            print("  Error: Incorrect file name")
                                        else:
                                            self.board.writeSudokuToCSV(fname, rows)    
                                            print("Output File " + fname + " written !")
                                            break
                                    input("press any key to continue ")                       
                                case "h":
                                    print("""
        ***** Help *****
        press     h for help
                  s for shuffling strategies
                  n for noninteractive mode
                  a for activating Monitoring
                  d for deactivating Monitoring
                  b to  save state in stack
                  w to  write Sudoku puzzle to a file
                  i to  inspect the current board w.r.t. influencers
                  c to  inspect the current board w.r.t. candidates
                  q to  quit this loop
                                    """)
                                    input("press any key to continue ")
                                case "a": 
                                    self.monitoringActive = True
                                    print("Monitoring activated")
                                case "d":
                                    self.monitoringActive = False
                                    print("Monitoring deactivated")
                                case "i":
                                    self.printCandidatesAndInfluencers(candidates = False, title="LIST OF INFLUENCERS")
                                case "c":
                                    self.printCandidatesAndInfluencers(candidates = True, title="LIST OF CANDIDATES")
                                    #input("press any key to continue ")
                                case "s":
                                    print("Shuffling all strategies ...")
                                    shuffle(self.occupationStrategies)
                                    shuffle(self.influenceStrategies)
                                case "n":
                                    print("Enabling noninteractive mode ...")
                                    info = Info.NONE
                                case other: 
                                    print("press q or any other key to quit")
                            print()

                        self.occupy(n, i, j) # occupy it
                        self.steps += 1 # increase step counter
                        changes += 1 # increase change counter

                        if (info == Info.PRETTY) or (info == Info.NONE):
                            self.prettyPrint(self.convertToIntArray())
                        else:
                            self.displayBoard(info) # display board
                        print("STEP: " + str(self.steps)) # display step
                        print()
            if changes == 0: # no changes => cannot solve board any further 
                    print("I am stuck: cannot solve remaining cells with existing strategies.")
                    print("Candidates Listing for manual analysis:")
                    self.printCandidatesAndInfluencers(candidates = True, title="LIST OF CANDIDATES")        
                    ready = False
                    print("(sudokuSolver): Enter w to write state to file, q to quit ")
                    while not ready:
                        value = input(" ---> ")
                        match value:
                            case 'q': 
                                ready = True
                            case 'w':
                                rows = self.board.turnBoardIntoList()
                                while True:
                                    fname = input("* Enter name of output file: ")   
                                    if os.path.isfile(fname):
                                        print("  Error - file already exists. Use another filename.")
                                        continue
                                    elif len(fname) == 0:
                                        print("  Error: Incorrect file name")
                                        continue
                                    else:
                                        self.board.writeSudokuToCSV(fname, rows)    
                                        print("Output File " + fname + " written !")
                                        ready = True
                                        break
                                input("press any key to continue ")
                    return False
        if (self.isCompleted()): # successful completion of loop
            print("Success: board solved")
            return True
        else: 
            return False
            
"""
The class PointingPairsAndTriplesStrategy implements an 
Influence Strategy. If only 2 (or 3) cells in a quadrant 
have the candidate c and f all these cells are located
in the same row (or column), then c cannot be a candidate
in any remaining cells of this row (or column).
In contrast to other strategies this stratgey is 
provided as an external class instead of an internal
class of SudokuSolver.

"""
class PointingPairsAndTriplesStrategy(InfluenceStrategy):
    def __init__(self, board):
        self.board = board
        
    def applyStrategy(self):
        self.applyStrategyToQuadrants()
        
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
                
            if count >= 2:
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
                            
                        
    def applyStrategyToQuadrants(self):
        # for all quadrants (d1,d2):
        for d1 in range(1, dim+1):
            for d2 in range(1, dim+1):
                array = []
                for r in range(1, dim+1):
                    for c in range(1, dim+1):
                        # and append the cells to array
                        array.append(((d1-1) * dim + r, (d2-1) * dim + c))
                # iterate through all possible numbers
                for n in range(1, DIM+1):
                    self.handlePointingPairsAndTriples(array, n)
            

