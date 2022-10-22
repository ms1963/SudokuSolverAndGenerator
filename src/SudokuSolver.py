"""
#############################################################
Sudoku Solver and Generator, (c) 2022 by Michael Stal
contains the classes SudokuSolver and SudokuGenerator
requires: Python version >= 3.10
-------------------------------------------------------------
applicable to standard Sudoku board with 9 x 9 positions and
digits in {1,2, ..., 9}
=============================================================
This package consist of the three core classes:

    SudokuSolver 
        and
    SudokuGenerator
        and
    SudokuShell.
    
The first one (SudokuSolver) helps solving Sudoku puzzles 
(see above). 
The second one (SudokuGenerator) is used to create new 
Sudoku puzzles. Its output may be transformed to a 
string that may be used as input to SudokuSolver.
SudokuShell demonstrates how to use SudokuSolver and
SudokuGenerator in combination.

The method 

    demo() 
    
illustrates the usage of SudokuSolver a bit further.
            
#############################################################
"""

# dependencies:
import   csv
import   time
from     enum    import Enum, unique
from     random  import shuffle
import   copy
import   os.path

"""
WARNING: this code is not tested with dim other than 3. 
It might mot even work
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
    def __init__(self):
        self.reinitialize() # prepare board
        self.occupationStrategies = [] # init strategies
        self.influenceStrategies = []
        ## add strategies ## 
        
        # occupation strategies:
        
        strategy = self.OneCandidateLeftStrategy(self)
        self.attachOccupationStrategy(strategy)
        strategy = self.RemainingInfluencerStrategy(self)
        self.attachOccupationStrategy(strategy)
        strategy = self.DeepCheckStrategy(self)
        self.attachOccupationStrategy(strategy)
        
        # influence strategies
        strategy = self.IndirectInfluencersStrategy(self)
        self.attachInfluenceStrategy(strategy)
        strategy = self.XWingStrategy(self)
        self.attachInfluenceStrategy(strategy)
        strategy = self.SwordFishStrategy(self)
        self.attachInfluenceStrategy(strategy)
        
    # deletes and reinitializes self._data
    # Note: registered strategies are left untouched
    def reinitialize(self):
        self._data = []
        for i in range(0,DIM*DIM): # init all entries
            self._data.append((False,0,[]))

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
        # a result != 0, we found a number that may occupy
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
            
    
    ############# map methods ############# 
    
    # take user defined (i,j) and map it to internal index
    # into the one-dimensional list _data[0..DIM*DIM]
    def map(self, i, j):
        return (i - 1) * DIM + j - 1
    
    # take user-defined quardant-relative (d1, d2, xi, xj) and convert
    # it to internal index into one-dimensional list _data[0..DIM*DIM]
    def mapQuadrant(self, d1, d2, xi, xj):
        i = (d1-1)*dim + xi
        j = (d2-1)*dim + xj
        return self.map(i,j)
        
    # map internal index (to _data[0..DIM*DIM] to external coordinate
    # (i,j) with i, j starting from 1
    def inverseMapInternal(self, idx):
        i = idx // DIM + 1
        j = idx % DIM + 1
        return (i, j)
        
    # take board coordinate (i, j) and map it to 
    # quadrant-relative coordinate
    def inverseMapQuadrant(self, i, j):
        d1 = (i-1) // dim + 1
        d2 = (j-1) // dim + 1
        iq = i - (d1-1) * dim
        jq = j - (d2-1) * dim
        return (d1, d2, iq, jq)
        
    # map quadrant-relative coordinate to board-coordinate
    def inverseMap(self, d1, d2, r, c):
        return ((d1-1)*dim+r,((d2-1)*dim+c))
    
    ############# setter/getter methods ############# 
    # these methods in combination with the map()-methods 
    # build a wrapper over the low-level access to 
    # elements in _data[]
    
    # get content of field
    def getElement(self, i, j):
        return self._data[self.map(i,j)]
        
    # set element of field
    def setElement(self, i, j, xyz): 
        self._data[self.map(i,j)] = xyz
    
    # get content of field in quadrant
    def getElementInQuadrant(self, d1, d2, i, j):
        return self._data[self.mapQuadrant(d1,d2,i,j)]
        
    def setElementInQuadrant(self, d1, d2, i, j, xyz):
        self._data[self.mapQuadrant(d1,d2,i,j)] = xyz
        
    # get a row of the board with all information
    def getRow(self, row):
        result = []
        for col in range(1, DIM+1):
            (x,y,z) = self.getElement(row, col)
            result.append((x,y,z))
        return result
        
    # get a column of the board
    def getColumn(self, col):
        result = []
        for row in range(1, DIM + 1):
            (x,y,z) = self.getElement(row, col)
            result.append((x,y,z))
        return result
        
    # get a quadrant of the board
    def getQuadrant(d1, d2):
        resultlist = []
        for row in range(1, dim+1):
            temp = []
            for col in range (1, dim+1):
                cell = self.getElementInQuadrant(d1, d2, row, col) 
                tmp.append(cell)
            resultlist.append(tmp)
        return resultlist
                
    ############# vacancy/candidates/influencers methods ############# 
    
    # get all vacant cells of board 
    def getVacancies(self):
        vacancies=[]
        for row in range(1,DIM+1):
            for col in range(1, DIM+1):
                if not self.isOccupied(row, col):
                    vacancies.append((row, col))
        return vacancies
    
    # get vacant neighbor cells in quadrant defined by (i,j)        
    def getVacanciesInQuadrant(self, d1, d2, r, c):
        vacancies =    []
        for row in range(1,dim+1):
            for col in range(1, dim+1):
                if (row, col) == (r, c): continue
                (x, y, z) = self.getElementInQuadrant(d1,d2, row, col)
                if x: continue
                else: vacancies.append((row, col))
        return vacancies
                
    # get vacant neighbor cells in row i
    def getVacanciesInRow(self, i, j):
        vacancies =   []
        for col in range(1, DIM+1):
            if col == j: continue
            (x, y, z) = self.getElement(i, col)
            if x: continue
            else: vacancies.append((i,col))
        return vacancies
        
    # get vacant neighbor cells in column j
    def getVacanciesInColumn(self, i, j):
        vacancies =   []
        for row in range(1, DIM+1):
            if row == i: continue
            (x, y, z) = self.getElement(row, j)
            if x: continue
            else: vacancies.append((row, j))
        return vacancies
        
    # return number in cell(i,j) if available,
    # otherwise return 0
    def getOccupant(self, i, j):
        (x, y, z) = self.getElement(i,j)
        if x: 
            return y
        else: 
            return 0
            
    # which other numbers already dominate this position?
    # => these numbers are no candidates for this field        
    def getInfluencers(self, i, j):
        (x, y, z) = self.getElement(i,j)
        if not x:
            return z
        else: 
            return []
       
    # get potential candidates for this location
    def getCandidates(self, i, j):
        (x,y,z) = self.getElement(i,j)
        if x: # occupied locations neither have 
              # influencers nor candidates
            return []
        else:
            infl = self.getInfluencers(i,j)
            candidates = []
            for num in range (1, DIM+1):
                if not num in infl:
                    candidates.append(num)
            return candidates
            
    # calculate candidates from currently known influencers
    def calcCandidates(self, z):
        candidates = []
        for num in range (1,DIM+1):
            if not num in z:
                candidates.append(num)
        return candidates       
        
    ############# occupy methods ############
        
    # which number must be placed in this location?
    # Returns 0 if no number can be placed since location  
    # is already occupied or more than one number is possible
                    
    def canBeOccupied(self, i, j):
        retVal = (0, "")
        (x, y, z) = self.getElement(i,j) # get entry
        if not x:
            for strategy in self.occupationStrategies:
                result = strategy.applyStrategy(i,j)
                if result != 0: 
                    retVal = (result, str(strategy))
                    break
        return retVal
                   
    # occupy field with number
    # set surpress to True to prevent information abour
    # called InfluenceStrategies
    def occupy(self, number, i, j):
        # get internal data for (i,j)
        (x, y, z) = self.getElement(i,j)
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
            self.setElement(i,j, (x,y,z)) # update _data[]
            if not self.checkConformanceOfBoard(): # check for conformance
                print("Error: rule violation in (" + str(i) + "," + str(j) + ") when entering " + str(number))
                print("Restoring previous content")
                (x, y, z) = (x_old, y_old, z_old)
                self.setElement(i,j,(x,y,z))
            else:
                # reanalyze the board, as some influencers have been 
                # introduced by occupying (i,j), so that the occupation
                # strategies work
                self.addInfluencersToBoard(number, i, j)
                # call all strategies which may remove candidates
                # from some cells which is equivalent to adding
                # influencers
                for strategy in self.influenceStrategies:
                    strategy.applyStrategy()
    
    # is position occupied. Other method would be 
    # to check for not ((i,j) in vacancies)        
    def isOccupied(self, i, j):
        (x, y, z) = self.getElement(i,j)
        return x        

        
    ############# add influencer  methods ############# 
    
    # add additional influencer to single cell(i,j)
    def addInfluencer(self, number, i, j):
        (x, y, z) = self.getElement(i,j)
        if not x: # location is not occupied 
            if not (number in z): # if not already in list
                z.append(number) # add it to list
                self.setElement(i,j,(x, y, z))
           
    # add influence to quadrant
    def addInfluencerToQuadrant(self, number, d1, d2):
        quad_row = (d1-1) * dim
        quad_col = (d2-1) * dim
        
        for i in range(1, dim+1):
            for j in range(1, dim+1):
                self.addInfluencer(number, quad_row+i, quad_col+j)
                   
    # add influences of number in (i,j)                
    def addInfluencersToBoard(self, number, i, j):
        (d1, d2, r, c) = self.inverseMapQuadrant(i, j)
        self.addInfluencerToQuadrant(number, d1, d2)
        self.addInfluencerToRow(number, i)
        self.addInfluencerToColumn(number, j)
    
    # add number as influencer to column j with the exceptions stated 
    # by the exceptionList
    def addInfluencerToColumn(self, number, j, exceptionList = []):
        for i in range(1, DIM+1):
            if not (i in exceptionList):
                (x,y,z) = self.getElement(i,j)
                if not x:
                    self.addInfluencer(number, i, j)

    # add number as influencer to row i with the exceptions stated 
    # by the exceptionList
    def addInfluencerToRow(self, number, i, exceptionList = []):
        for j in range(1, DIM+1):
            if not (j in exceptionList):
                (x,y,z) = self.getElement(i,j)
                if not x:
                    self.addInfluencer(number, i, j)
        
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

            
    ############# Indirect Influencers Strategy ############ 
            
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
        
    ############# check conformance methods ############# 
    
    # check whether row conforms to rules, i.e., whether
    # there are duplicates in a row               
    def checkConformanceInRow(self, r):
        numberList = []
        for c in range(1,DIM+1):
            (x,y,z) = self.getElement(r,c)
            if x:
                if y in numberList:
                    print("Conflict: " + str(y) + " found twice in row " + str(r))
                    return False
                else:
                    numberList.append(y)
            else:
                continue 
        return True
    
    # check whether column conforms to rules, i.e., whether
    # there are duplicates in a column
    def checkConformanceInColumn(self, c):
        numberList = []
        for r in range(1,DIM+1):
            (x,y,z) = self.getElement(r,c)
            if x:
                if y in numberList:
                    print("Conflict: " + str(y) + " found twice in column " + str(c))
                    return False
                else:
                    numberList.append(y)
            else:
                continue
        return True
        
    # check whether quadrant conforms to rules, i.e., whether
    # there are duplicates in the quadrant
    def checkConformanceInQuadrant(self, d1, d2):
        numberList = []
        quadTop = (d1-1)*dim + 1
        quadLeft = (d2-1)*dim + 1
    
        for i in range(0, dim):
            for j in range(0, dim):
                (x,y,z) = self.getElement(quadTop + i, quadLeft + j)
                if x:
                    if y in numberList:
                        print("Conflict: " + str(y) + " found twice in quadrant (" + str(d1) + "," + str(d2) + ")")
                        return False
                    else:
                        numberList.append(y)
                else:
                    continue
        return True
                           
    # check whether whole board complies with rules, i.e., whether
    # all columns, rows, and quadrants conform to rules
    def checkConformanceOfBoard(self):
        for c in range(1, DIM+1):
            if not self.checkConformanceInColumn(c):
                return False
        for r in range(1, DIM+1):
            if not self.checkConformanceInRow(r):
                return False
        for d1 in range(1, dim+1):
            for d2 in range(1, dim+1):
                if not self.checkConformanceInQuadrant(d1,d2):
                    return False
        return True
    
    ############# display methods ############# 
             
    # display whole board 
    # Info.ALL  => print all data 
    # Info.INFLUENCERS => print influencers 
    # Info.OCCUPANTS => print occupants       
        
    def displayBoard(self, info = Info.ALL):
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
                        print("[" + str(k) + ":" +str(l) + "] =", end = " ")
                        print("(" + str(y) + " *)", end = " ")
                    elif info == Info.CANDIDATES:
                        print("[" + str(k) + ":" +str(l) + "] =", end = " ")
                        print("(" + str(y) + " *)", end = " ")
                    else:
                        print(" " + str(y) + " ",end = " ")
                else:
                    if info == Info.ALL:
                        print("[" + str(k) + "," +str(l) + "] z = " + str(z), end = " " )
                        print(x,y,z);
                    elif info == Info.INFLUENCERS:
                        print("[" + str(k) + ":" +str(l) + "] =", end = " ")
                        print(z, end = " ")
                    elif info == Info.CANDIDATES:
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
        
    ############# prettyPrint method ############## 
    
    # using convertToIntArray _data[] is converted
    # to a two dimensional array of ints.
    # this array can be printed using prettyPrint()
    def convertToIntArray(self):
        intarray = []
        for i in range(1, DIM+1):
            row = []
            for j in range(1, DIM+1):
                row.append(self.getOccupant(i,j))
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
            
        
    ############# conversion methods   ############# 
    
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
        self.vacancies = self.getVacancies()
                        
    # create string list from the current board
    def turnBoardIntoString(self):
        sl = ""
        for idx in range(0, DIM*DIM):
            (x,y,z) = self._data[idx]
            if x:
                sl += str(y)
            else:
                sl += str(0)
        return sl
            
    ############# file I/O methods #############   
          
    # take the current Sudoku Board and convert it to list.
    # operation does only work if board is conformant to rules
    def turnBoardIntoList(self):
        if self.checkConformanceOfBoard():
            rows=[]
            for i in range(0, DIM*DIM):
                (x,y,z) = self._data[i]
                if x:
                    rows.append(y)
                else:
                    rows.append(0)
            return rows
        else:
            return []
        
    # take a one-dimensional list and convert it to Sudoku board 
    # but only if board conforms to Sudoku rules
    def turnListIntoBoard(self, rows):
        _data = self._data
        self.reinitialize()
        for i in range(0, DIM*DIM):
            num = rows[i]
            if num != 0:
                self.occupy(num, i // DIM + 1, i % DIM + 1)
        if not self.checkConformanceOfBoard(): # if invalid board
            self._data = _data # restore old state
        self.vacancies = self.getVacancies()
    
    # existing Sudoko board is read from CSV file and returned as 
    # a list (one-dimensional)
    # 
    def readSudokuFromCSV(self, filename):
        csv.register_dialect('excel', delimiter=';', quoting=csv.QUOTE_NONE)
        counter = 0
        rows = []

        with open(filename, newline='') as f:
            try: 
                reader = csv.reader(f, delimiter=";")
                print("... reading file " + filename + " ...")
                print()
                i = 0;
                for row in reader:
                    counter +=1;
                    if len(row) != DIM:
                        print("Error: row " + str(counter) + " requires " + str(DIM) + " entries")
                        return []
                    for j in range(0, DIM):
                        rows.append(int(row[j]))
            
                if counter != DIM:
                    print("Error: " + str(DIM) + " rows expected, not " + str(counter))
                    return []
                
            except csv.Error as e:
                print('file {}, line {}: {}'.format(filename, reader.line_num, e))
        
        return rows
        
    # write board given as rows to file using CSV-format.    
    # one-dimensional row representing Sudoku board is stored 
    # to CSV file using Excel-format 
    # for example:
    # 1; 0; 3; 0; 0; 0; 0; 0; 0 
    # 2; 1; 4; 0; 0; 0; 0; 0; 0 
    # .
    # . 
    # . 
    # . 
    # . 
    # . 
    # 0; 3; 1; 0; 0; 4; 7; 0; 0
    # => DIM rows with DIM elements per row
    def writeSudokuToCSV(self, filename, rows):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';',quoting=csv.QUOTE_NONE)
            # cut rows in pieces 
            print("... writing file " + filename + "...")
            print()
      
            idx = 0
            while idx < DIM * DIM:
                row = []
                for i in range(0, DIM):
                    row.append(rows[i + idx])
                writer.writerow(row)
                idx += 9    
                
    ############# helper methods #############  
    
    # create list of all possible numbers between
    # 1 and DIM
    def fullListOfNumbers():
        return [num for num in range(1, DIM+1)]
        
        
    # find first vacancy using internal _data[]
    # structure
    def findFirstVacancy(self):
        for idx in range(0, DIM*DIM):
            (x,y,z) = self._data[idx]
            if not x:
                return self.inverseMapInternal(idx)
        return (0,0)
                
    ############# solver methods ############# 

    # checks whether all cells are occupied 
    # can also checked with vacancies == [] instead
    def isCompleted(self):
        for idx in range(0, DIM*DIM):
            (x,y,z) = self._data[idx]
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
        if not self.checkConformanceOfBoard(): # board must conform to rules
            print ("Error: board does not conform to Sudoku rules")
            return
        self.steps = 0
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
                        print("Strategy used = " + msg)                     
                        if info != Info.NONE:   
                            value = input("SudokuSolver: Enter <any key> to continue, q to quit, h to display help ---> ")
                            print()
                            match value:
                                case "q": 
                                    print("Exiting from SudokuSolver ...")
                                    return
                                case "w":
                                    rows = self.turnBoardIntoList()
                                    while True:
                                        fname = input("* Enter name of output file: ")   
                                        if os.path.isfile(fname):
                                            print("  Error - file already exists. Use another filename.")
                                        elif len(fname) == 0:
                                            print("  Error: Incorrect file name")
                                        else:
                                            self.writeSudokuToCSV(fname, rows)    
                                            print("Output File " + fname + " written !")
                                            break
                                    input("press any key to continue ")
                                case "h":
                                    print("***** Help *****")
                                    print("press h for help")
                                    print("press s for shuffling occupation strategies")
                                    print("press n for noninteractive mode")
                                    print("press w to  write Sudoku puzzle to a file")
                                    print("press i to  inspect the current board w.r.t. influencers")
                                    print("press c to  inspect the current board w.r.t. candidates")
                                    print("press q to  quit this loop")
                                    print()
                                    input("press any key to continue ")
                                case "i":
                                    print("### INFLUENCERS ###") 
                                    print("[4:8]        => row 4, column 8")
                                    print("(7 *)        => occupied with 7")
                                    print("[1, 2, 5, 7] => influencers 1, 2, 5 and 7")
                                    print()                                      
                                    self.displayBoard(info.INFLUENCERS)
                                    input("press any key to continue ")
                                case "c":
                                    print("### CANDIDATES ###")
                                    print("[4:8]        => row 4, column 8")
                                    print("(7 *)        => occupied with 7")
                                    print("[1, 2, 5, 7] => candidates 1, 2, 5 and 7")
                                    print()                                             
                                    self.displayBoard(info.CANDIDATES)
                                    input("press any key to continue ")
                                case "s":
                                    print("Shuffling strategies ...")
                                    shuffle(self.occupationStrategies)
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
                    print("Error: cannot solve remaining cells with existing strategies.")
                    print("Candidates Listing for manual analysis:")
                    print("[4:8]        => row 4, column 8")
                    print("(7 *)        => occupied with 7")
                    print("[1, 2, 5, 7] => candidates 1, 2, 5 and 7")
                    print()    
                    self.displayBoard(info.CANDIDATES)
                    return False
        if (self.isCompleted()): # successful completion of loop
            print("Success: board solved")
            return True
        else: 
            return False

"""           
######################################################################           
The class SudokuGenerator contains the method 
        createSudoku(self, minimumDependeny)
that creates a new Sudoku puzzle that only has one unique solution. 
In the argument minimumDependeny users can specify how many cells
should be occupied (recommendation: use >= 17). 
The method returns a Sudoku puzzle as an two-dimensional array of cells
with numbers. 
Using the method 
        turnIntoString(self, board)
the board may be transformed into a string to be used as an input
for class SudokuSolver.        
######################################################################
"""

class SudokuGenerator:   
    ########## obtaining initial configuration  ##########
    # sets number of solutions to 0 
    # creates a board with zeros
    # calls createSudoku
    def reinitialize(self):
        self.noOfSolutions = 0
        # generate a Sudoku puzzle
        self.board = [[0 for row in range(DIM)] for col in range(DIM)]
        
    ########## creation of a new puzzle ##########

    # createSudoku() creates a solution for the previously
    # empty board
    def createSudoku(self, minimumOccupancy = 20):
        self.reinitialize()
        # create a full solution
        self.createSolution(self.board)
        self.eliminateNumbers(minimumOccupancy = 20)
        return self.board
        
    ########## transformation of Sudoku board to a string ##########
    # this method transforms the board to a string
    def turnIntoString(self, board):
        string = ""
        for i in range(DIM):
            for j in range(DIM):
                string += (str(board[i][j]))
        return string

    ########## check whether number can be used ##########
    def canBeUsed(self, board, number, row, col):
        # is the number already available in row
        if number in board[row]:
            return False
        # is the number already available in column
        for i in range(DIM):
            if board[i][col] == number:
                return False
        # is the number already available in the quadrant
        quadRow = (row // dim) * dim
        quadCol = (col // dim) * dim
        for i in range(quadRow, (quadRow + dim)): 
            for j in range(quadCol, (quadCol + dim)): 
                if board[i][j] == number: 
                    return False
        # if we didn't find number in row, col, or quadrant, 
        # we return True. number can be entered in (row, col)
        return True

	########## search for next vacant cell ##########
    def nextVacantCell(self,board):
        # search the board for a vacant cell
        for i in range(DIM):
            for j in range(DIM):
                # if a vacant cell is found, 
                # we return it to the caller
                if board[i][j] == 0:
                    return (i,j)
        return

    ########## solving the Sudoku puzzle ##########
    def solve(self, board):
        # create a list of all numbers from 1 to DIM
        numbers = [n for n in range(1, DIM+1)]
        for i in range(0,DIM * DIM):
            row = i // DIM 
            col = i  % DIM
            #find next empty cell
            if board[row][col] == 0:
                for number in numbers:
                    # ensure number is not an influencer
                    if self.canBeUsed(board,number,row,col):
                        # if it isn't, we can pit number into (i,j)
                        board[row][col]=number
                        # check for the next vacant sell
                        if not self.nextVacantCell(board):
                            # if there are none, we are done,
                            # since we found a(nother) solution
                            self.noOfSolutions += 1
                            break
                        else: # there is a vacant cell => continue
                            if self.solve(board):
                                return True
                break
        # reset cell to 0 and return False since 
        # we couldn't solve the board with the selected entry
        # in (row,col)
        board[row][col]=0  
        return False

    ########## creation of a solution ##########
    def createSolution(self, board):
        # create a list of all numbers from 1 to DIM
        numbers = [n for n in range(1, DIM+1)]
        # iterate the board
        for i in range(0,DIM * DIM):
            row = i // DIM
            col = i  % DIM
            # query next empty cell
            if board[row][col] == 0:
                # shuffle numbers for randomization
                shuffle(numbers)      
                # try number for number
                for number in numbers:
                    # can number  be used in (row, col)
                    if self.canBeUsed(self.board,number,row,col):
                        # if yes, put the number into the cell
                        board[row][col]=number
                        # are there any vacant cells
                        if not self.nextVacantCell(board):
                            # if not, we are done
                            return True
                        else: # there is a vacant cell 
                            # => continue the recursion
                            if self.createSolution(board):
                                # if the grid is full
                                return True
                break
        # clear (row,col) as we did not succeed with any number
        board[row][col] = 0  
        return False
        
    ########## retrieving all cells that are occupied ##########

    def getOccupiedCells(self,board):
        """returns a shuffled list of non-empty squares in the puzzle"""
        occupiedCells = []
        # iterate the whole board
        for i in range(DIM):
            for j in range(DIM):
                # if cell is occupied
                if board[i][j] != 0:
                    # add it to the list of occupied cells
                    occupiedCells.append((i,j))
        # shuffle occupied cells for randomization
        shuffle(occupiedCells)
        return occupiedCells
        
    ########## elimination of numbers from solution ##########

    def eliminateNumbers(self, minimumOccupancy = 17):
        # retrieve all occupied cells
        occupiedCells = self.getOccupiedCells(self.board)
        noOfOccupiedCells = len(occupiedCells)
        iters = 4
        while iters > 0 and noOfOccupiedCells >= minimumOccupancy:
            # retrieve the next occupied cell 
            row,col = occupiedCells.pop()
            # reduce number accordingly
            noOfOccupiedCells -= 1
            # backup cell for the case 
            # that there are multiple solutions
            savedCell = self.board[row][col]
            # clear cell
            self.board[row][col] = 0
            # make a copy to be used for the recursive call
            board_copy = copy.deepcopy(self.board)
            # initialize noOfSolutions counter to zero
            self.noOfSolutions = 0 
            # try to solve Sudoku     
            self.solve(board_copy)   
            # roll back if there are multiple solutions
            if self.noOfSolutions != 1:
                self.board[row][col] = savedCell
                noOfOccupiedCells += 1
                iters -= 1
        return

    # prettyPrint displays the Sudoku board in a textual
    # but nice way
    def prettyPrint(self, s, title = ""):
        def createLine(row):
            return row[0]+row[5:9].join([row[1:5]*(dim-1)]*dim)+row[9:13]
        
        board = []
        for i in range(0, DIM):
            row = []
            for j in range(0, DIM):
                cell = int(s[i * DIM + j])
                row.append(cell)
            board.append(row)
            
        print(title)
        
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


        
################## class SudokuShell ################## 
# this class illustrates how to use the classes
# SudokuSolver and SudokuGenerator in conjunction 
# for creating and solving Sudoku puzzles
# Its only method run() is intended as a command
# shell that listens to user commands. 
# q  <ret> quits the shell.
# <ret> or any other character <ret> start 
# a new puzzle.
# It is implemented as a Singleton

class SudokuShell:
    # no __init__ constructor needed
    _instance = None
    def __new__(cls):
        if cls._instance == None:
            cls._instance = super(SudokuShell, cls).__new__(cls)
        return cls._instance
        
    def run(cls):
        strategiesAlreadyDisplayed = False
        while True:
            print("###########################################################")

            value = input("SudokuShell: Enter any key to start new Sudoku puzzle, or q to quit ---> ")
            print()
            match value:
                case "q":
                    print("Exiting from SudokuShell ...")
                    break
                
            # instantiate a new solver
            solver = SudokuSolver()
            if not strategiesAlreadyDisplayed:
                print("Identifying installed strategies")
                print("Occupation Strategies:")
                for strategy in solver.getInstalledOccupationStrategies():
                    print(strategy)
                print("Influence Strategies:")
                for strategy in solver.getInstalledInfluenceStrategies():
                    print(strategy)
                strategiesAlreadyDisplayed = True
            # instantiate a new generator
            generator = SudokuGenerator()
            print()
            # create a new puzzle 
            board = generator.createSudoku(minimumOccupancy = 17)
            # turn the board into a string
            intarray = generator.turnIntoString(board)
            # turn  the intarray to an internal data structure
            # the solver understands
            solver.turnStringIntoBoard(intarray)
            # call the solver to solve the puzzle
            solver.solve(Info.PRETTY)
            print()
            
            
"""
#############################################################
Demo code used to check SudokuSolver and SudokuGenerator
#############################################################
"""
               
#####################################################################
# the function demo() is used to test the SudokuSolver implementation
# mode 0: read Sudoko from CSV file 
# mode 1: programmatically configure Sudoku 
# mode 2: read board configuration from string list
def demo(mode = 0):
    board = SudokuSolver()
    
    match mode:
        case 0:
            # read puzzle from file demo.csv
            rows = board.readSudokuFromCSV("demo.csv")
            # adapt the result for the SudokuSolver
            board.turnListIntoBoard(rows)
            # and let it solve the puzzle
            res = board.solve(Info.PRETTY)
            if res: # on success
                print("Board solved")
            else: # on failure
                print(f"Board not solved after {board.steps} steps")
                # print cells that were left vacant
                print("Remaining cells:")
                print(board.getVacancies())
        case 1:   # mode == 1:
            # occupy various cells
            board.occupy(2, 1, 2) # row 1
            board.occupy(1, 1, 4)
            board.occupy(7, 1, 5)
            board.occupy(9, 1, 6)
            board.occupy(5, 1, 8)
    
            board.occupy(5, 2, 5) # row 2
            board.occupy(6, 2, 7)
    
            board.occupy(9, 3, 8) # row 3
            board.occupy(3, 3, 9)
    
            board.occupy(2, 4, 1) # row 4
            board.occupy(4, 4, 7)
            board.occupy(7, 4, 9)
    
            board.occupy(5, 5, 3) # row 5
            board.occupy(6, 5, 6)
            board.occupy(1, 5, 8)
    
            board.occupy(9, 6, 1) # row 6
            board.occupy(7, 6, 2)
            board.occupy(2, 6, 7)
            board.occupy(3, 6, 8)
    
            board.occupy(2, 7, 6) # row 7
    
            board.occupy(1, 8, 5) # row 8
            board.occupy(7, 8, 7)
            board.occupy(2, 8, 8)
    
            board.occupy(1, 9, 2) # row 9
            board.occupy(3, 9, 4)
            # solver start
            res = board.solve(Info.PRETTY)
            if res: # on success
                print("Board solved")
            else: # on failure
                print(f"Board not solved after {board.steps} steps")
                print("Remaining cells:")
            # print cells that were left vacant
            print(board.getVacancies())
        case 2:
            # create SokukuGenerator instance
            sg = SudokuGenerator()
            # create Sudoku puzzle with minimumOccupancy
            bd = sg.createSudoku(17)
            # turn the board into a string
            sl = sg.turnIntoString(bd)
            # and print the board
            sg.prettyPrint(sl, "Sudoku Initial Configuration")
            # let puzzle be solved and the runtime be measured
            startT = time.time()
            sol = board.solveBF(sl)
            endT = time.time()
            # print solution
            sg.prettyPrint(sol, "Sudoku Solution")
            print("Time spent for brute force algorithm (in secs): " + str(endT-startT))
        case other:
            # instantiate SudokuGenerator
            sg = SudokuGenerator()
            # create a fully occupied Sudoku board
            # which is then turned into a puzzle by 
            # removing occupied cells down to a 
            # minimum.
            bd = sg.createSudoku(minimumOccupancy = 17)
            # transform the number-list returned by
            # SudokuGenerator into a string
            sl = sg.turnIntoString(bd) 
            # turn this string into a board 
            board.turnStringIntoBoard(sl)
            # and call solve() within Sudoku
            board.solve(Info.PRETTY)
    
    
# ENTRY POINT    
 
if __name__ == "main":
    print("Started from Command Line Interface")
    print("Sudoku Solver & Generator (c) 2022 by Michael Stal")
    
    # Using SudokuSolver as an interactive shell 
    # which generates Sudoku puzzles which it then
    # tries to solve. It is called by 
    # <instance>.run()

    shell = SudokuShell()
    shell.run()
    
    # in demo the test code gets called   
    # mode == 0: read board from CSV file 
    # mode == 1: set cells programmatically
    # mode == 2: demonstrate the Sudoku Generator
    # mode == 3: read Sudoku from string 
    
    demo(mode = 2)

"""
else:
    demo(1)
    shell = SudokuShell()
    shell.run()
"""

    

