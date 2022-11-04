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
This package consist of the core classes

    Board
    Links
    
    
    
Board maintains the Sudoku board. 
            
#############################################################
"""

# dependencies:
import   csv
from     copy    import copy, deepcopy


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

class Board:
    # self._data is an one-dimensional array that
    # stores all information for the Sudoku board. 
    # It consists of tuples (x, y, z)
    # x = True => position occupied by number y 
    # x = False=> position influenced by other numbers 
    #             defined in z without being occupied
    
    
    # call self.reinitialize() to delete _data[] and
    # initialize it with new values
    # and register required (predefined) strategies
    
    def __init__(self, data):
        self._data = data
        # self._links manages strong, weak and inner
        # links for strategies that use chaining
        self._links = None 
        
    # create weak, strong and inner links    
    def createLinks(self):
        self._links = Links(self)
        
    # stores a brute force solution used by Cheating
    def storeBFSolution(self, bfsolution):
        self.solution = bfsolution
    
    def turnMonitoringOn(self):
        self.monitoringActive = True
        
    def turnMonitoringOff(self):
        self.monitoringActive = False        
    
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
        
    # get a row of the board 
    def getRow(self, row):
        result = []
        for col in range(1, DIM+1):
            (x,y,z) = self.getElement(row, col)
            result.append((x,y))
        return result
        
    # get a column of the board
    def getColumn(self, col):
        result = []
        for row in range(1, DIM + 1):
            (x,y,z) = self.getElement(row, col)
            result.append((x,y))
        return result
        
    # get a quadrant of the board
    def getQuadrant(self,d1, d2):
        resultlist = []
        for row in range(1, dim+1):
            for col in range (1, dim+1):
                cell = self.getElementInQuadrant(d1, d2, row, col) 
                resultlist.append((cell[0], cell[1]))
        return resultlist
        
    # get the whole region that (i,j) can "see"
    def getRegion(self, i, j):
        resultList = []
        # get all cells in same row
        for col in range(1, DIM+1):
            resultList.append((i, col))
        # get all elements in same column
        for row in range(1, DIM+1):
            resultList.append((row, j))
        # get all elements in same quadrant 
        (d1,d2,r,c) = self.inverseMapQuadrant(i,j)
        for r_q in range(1, dim+1):
            for c_q in range(1, dim+1):
                resultList.append(((d1-1)*dim+r_q, (d2-1)*dim+c_q))
        return resultList
        
    # get the row a cell belongs to    
    def getRowOfCell(self, i, j):
        return self.getRow(i)
        
    # get the column a cell belongs to    
    def getColumnOfCell(self, i, j):
        return self.getColumn(j)
        
    # get the quadrant a cell belongs to
    def getQuadrantOfCell(self, i, j):
        (d1, d2, r, c) = self.inverseMapQuadrant(i,j)
        return self.getQuadrant(d1,d2)
        
                
    ############# vacancy/candidates/influencers methods ############# 
    
    # get all vacant cells of board 
    def getVacancies(self):
        vacancies=[]
        for row in range(1,DIM+1):
            for col in range(1, DIM+1):
                (x,y,z) = self.getElement(row,col)
                if not x:
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
        
    ############# same row, column, box ########### 
    
    # these simple methods check whether two cells 
    # are in the same row, column or quadrant
    def inSameRow(self, cell1, cell2):
        ic1, jc1 = cell1
        ic2, jc2 = cell2
        return ic1 == ic2 
        
    def inSameColumn(self, cell1, cell2):
        ic1, jc1 = cell1
        ic2, jc2 = cell2
        return jc1 == jc2 
        
    def inSameQuadrant(self, cell1, cell2):
        ic1, jc1 = cell1
        ic2, jc2 = cell2
        return (((ic1-1) / dim) == ((ic2-1) / dim)) and (((ic2-1) / dim) == ((ic2-1) / dim))

    def inSameRegion(self, cell1, cell2):
        return self.inSameRow(cell1, cell2) or self.inSameColumn(cell1, cell2) or self.inSameQuadrant(cell1, cell2)


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


    ############# check and search for candidates ########### 

    # expects a cell which is a tuple (row, col)
    # and checks whether cand is a candidate of cell
    def cellContainsCandidate(self, cell, cand):
        row,col = cell
        return cand in self.getCandidates(row,col)
        
    # check in an array of cells ( = (row,col) ) 
    # whether all cells contain cand as candidate
    def cellsContainCandidate(self, cells, cand):
        containCand = True
        for cell in cells:
            containCand = containCand and self.containsCandidate(cell, cand)
        return containCand
    
    # searches for common candidates in a list of cells
    def searchForCommonCandidates(self, cells):
        candList = {}
        for cand in range(1, DIM+1):
            if self.containCandidate(cells, cand):
                candList.add(cand)
        return candList
        
    # the following three methods check for cells of a 
    # row/column/quadrant that have n candidates
        
    def searchForNCandidatesInRow(self, n, row):
        assert n >= 0 and row <= 9, "n must be between 0 and 9"
        resSet = {}
        for col in range(1, DIM+1):
            candidates = self.getCandidates(row, col)
            if len(candidates) == n:
                resSet.add((row, col, set(candidates)))
        return resSet
                
    def searchForNCandidatesInColumn(self, n, col):
        assert n >= 0 and row <= 9, "n must be between 0 and 9"
        resSet = {}
        for row in range(1, DIM+1):
            candidates = self.getCandidates(row, col)
            if len(candidates) == n:
                resSet.add((row, col, set(candidates)))
        return resSet
                
    def searchForNCandidatesInQuadrant(self, n, d1, d2):
        assert n >= 0 and row <= 9, "n must be between 0 and 9"
        resSet = {}
        for row in range(1, dim+1):
            for col in range(1, dim+1):
                candidates = self.getCandidates((d1-1)*dim+row, (d2-1)*dim+col)
                if len(candidates) == n:
                    resSet.add(((d1-1)*dim+row, (d2-1)*dim+col, set(candidates)))
        return resSet
        
    # the next three methods check for cells in a row/column/quadrant 
    # that have only the specified candidates (set cands)
    def searchForCandidatesInRow(self, cands, row):
        assert n >= 0 and row <= 9, "n must be between 0 and 9"
        resSet = {}
        for result in self.searchForNCandidatesInRow(len(cands), row):
            (i, j, candSet) = result
            if candSet == cands:
                resSet.add((i,j))
        return resSet
        
    def searchForCandidatesInColumn(self, cands, col):
        assert n >= 0 and row <= 9, "n must be between 0 and 9"
        resSet = {}
        for result in self.searchForNCandidatesInColumn(len(cands), col):
            (i, j, candSet) = result
            # using set to avoid dependency on order of elements
            if candSet == cands:
                resSet.add((i,j))
        return resSet
        
    def searchForCandidatesInQuadrant(self, cands, d1, d2):
        resSet = {}
        for result in self.searchForNCandidatesInQuadrant(len(cands), d1, d2):
            (i, j, candSet) = result
            # using set to avoid dependency on order of elements
            if candSet == cands:
                resSet.add((i,j))
        return resSet

    
        
    ############# add influencer  methods ############# 
    # this strategy eliminates the need for some other
    # strategies such as PointingPairsAndTriples 
    
    # add additional influencer to single cell(i,j). Note: 
    # occupied cells are left untouched
    def addInfluencer(self, number, i, j):
        (x, y, z) = self.getElement(i,j)
        if not x: # location is not occupied 
            if not (number in z): # if not already in list
                z.append(number) # add it to list
                if self.monitoringActive:
                    self.setElement(i,j,(x, y, z))
                    print("addInfluencer called for (" + str(i) + "," + str(j) + ") adding " + str(number))
           
    # add influence to quadrant
    def addInfluencerToQuadrant(self, number, d1, d2, exceptionList = []):
        quad_row = (d1-1) * dim
        quad_col = (d2-1) * dim
        
        for i in range(1, dim+1):
            for j in range(1, dim+1):
                if (i,j) not in exceptionList:
                    self.addInfluencer(number, quad_row+i, quad_col+j)
                   
    # add influences of number in (i,j) without any exceptions
    # however, occupied cells are left untouched                
    def addInfluencerToRegionInclusive(self, number, i, j):
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
    
    # add influencers to region but do not change (i,j):                
    def addInfluencerToRegionExclusive(self, number, i, j):
        self.addInfluencerToRow(number, i, [j])
        self.addInfluencerToColumn(number, j, [i])
        self.addInfluencerToQuadrant(number, (i-1)//dim+1, (j-1)//dim+1, [(i,j)])
        

    

    # check whether board conforms to rules, i.e., whether
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
    
            
    
        
    ############# conversion methods   ############# 
    
    
                        
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
This package consist of the core class

    Links
    
    
    
Links provides functionality to store information about 
weak links, strong links, inner strong links.
It supports chaing strategies. Currently it is not used, 
and not integrated with the rest of the design, though.
            
#############################################################

The three lists managed by Links are two dimensional arrays
        weakLinks
        strongLinks
        innerLinks
where for example, strongLinks[num] (num in range(1, DIM+1))
contains all links regarding num as candidate.

Types used as entries in weakLinks[num], strongLinks[num], 
innerLinks[num]:
    
    For strong and weak links (strongLinks, weakLinks)
    an entry is a tuple
    
    (num, cell1, cell2) with  cell1 = (i1, j1), 
                              cell2 = (i2, j2)
    
            i1, j1, i2, j2 num in range(1, DIM+1)
    
    It defines a  strong or weak link from cell1 to 
    cell2 with respect to candidate num, i.e., num is 
    candidate in both cells, cell1 and cell2.
    
    For strong links this implies:
        If num is not the right number for cell1,  
        it must be the one set in cell2.
        Of course, it also implies the weaker
        condition: if num is the right candidate
        for cell1, it can't be a candidate in cell2.
        
    For weak links this implies: 
        If num is the right candidate for cell1, it 
        cannot be a candidate in cell2. However, it 
        does NOT imply: if num is not the right 
        candidate for cell1, then it must be a 
        candidate in cell2. This holds, because weak 
        links imply that there are further cells in 
        the sam row,  column, quadrant that also 
        contain num as candidate. 
        
        
    
    For inner strong links (innerLinks) the entry is:
        
    (cell, num1, num2) with cell = (i, j)
    
            i, j, num1, num2 in range (1, DIM+1)
    
        i.e., num1 and num2 are the only  
        candidates of the cell. If num1 is not 
        the right candidate for the cell, then 
        num2 must be the right one, and vice
        versa.
    
"""


class Links:
    def __init__(self, board):
        self.board = board # board with all the data
        self.reinitialize() # continue initialization

    # complete clean up of tables
    def reinitialize(self):
        # List of weak links with number as array index
        self.weakLinks = [[] for num in range(1, DIM+1)]
        # List of strong links with number as array index
        self.strongLinks = [[] for num in range(1, DIM+1)]
        # List of strong links within a cell
        self.innerLinks = [[] for num in range(1, DIM+1)]
        
    # helper method that expects the candidate num and a list 
    # of cells, and figures out all cells in which num is a 
    # candidate
    def findCandidateInCells(self, num, cells):
        cellsWithCandidate = []
        for (i,j) in cells: # iterate all cells 
            # is num a candidate in this cell?
            if num in self.board.getCandidates(i, j):
                # yes, then store it in list
                cellsWithCandidate.append((i,j))
        # return list of cells with num as candidate
        return cellsWithCandidate
                
    # this method is the heart of the whole class. It is 
    # responsible to update strongLinks, weakLinks, and innerLinks
    # cells contains all the cells to analyze
    def enterLinks(self, cells):
        # iterate through all numbers/candidates
        for num in range(0, DIM+1):
            # find all cells in these cells that contain num 
            # as candidate
            cellsWithCandidate = self.findCandidateInCells(num, cells)
            # if there are only two cells in the row, column, or quadrant, 
            # we have found a strong link wrt. num
            if len(cellsWithCandidate) == 2:
                # both directions are a strong link
                link1 = (num, cellsWithCandidate[0], cellsWithCandidate[1])
                link2 = (num, cellsWithCandidate[1], cellsWithCandidate[0])
                # thus, append these links to the strongLink
                # section of candidate num
                self.strongLinks[num].append(link1)
                self.strongLinks[num].append(link2)
                # now let us analyze whether there is a cell 
                # that only contains 2 candidates. If yes, we got
                # strong links between two candidates of the same cell
                (i1, j1) = link1
                (i2, j2) = link2
                # we check this for both cells
                candsInCell1 =  self.board.getCandidates(i1,j1)
                candsInCell2 =  self.board.getCandidates(i2,j2)
                # cell number 1
                if len(candsInCell1) == 2:
                    cand1 = candsInCell1[0]
                    cand2 = candsInCell1[1]
                    self.innerLinks[cand1].append(((i1, j1), cand1, cand2))
                    self.innerLinks[cand2].append(((i1, j1), cand2, cand1))
                # and number 2
                if len(candsInCell2) == 2:
                    cand1 = candsInCell2[0]
                    cand2 = candsInCell2[1]
                    self.innerLinks[cand1].append(((i1, j1), cand1, cand2))
                    self.innerLinks[cand2].append(((i1, j1), cand2, cand1))
            # if there are more than two cells with the same candidate, each
            # pair defines a weak link w.r.t. num
            elif len(cellsWithCandidate) > 2:
                # now let us analyze al combinations of pairs
                for n1 in range(0, len(cellsWithCandidate)-1):
                    for n2 in range(n1+1, len(cellsWithCandidate)):
                        # get cell n1 and cell n2
                        cell1 = cellsWithCandidate[n1]
                        cell2 = cellsWithCandidate[n2]
                        # from which we can derive two weak links 
                        # link1 and link2
                        link1 = (num, cell1, cell2)
                        link2 = (num, cell2, cell1)
                        # add both to the respective element weakLinks
                        self.weakLinks[num].append(link1)
                        self.weakLinks[num].append(link2)
                        # and look for cells with only two candidates
                        # that can serve as inner strong links
                        if len(candsInCell1) == 2:
                            cand1 = candsInCell1[0]
                            cand2 = candsInCell1[1]
                            self.innerLinks[cand1].append(((i1, j1), cand1, cand2))
                            self.innerLinks[cand2].append(((i1, j1), cand2, cand1))
                        if len(candsInCell2) == 2:
                            cand1 = candsInCell2[0]
                            cand2 = candsInCell2[1]
                            self.innerLinks[cand1].append(((i1, j1), cand1, cand2))
                            self.innerLinks[cand2].append(((i1, j1), cand2, cand1))
    
    
    # search all rows for links    
    def searchRowsForLinks(self):
        for row in range(1, DIM+1):
            cells = self.board.getRow(row)
            self.enterLinks(cells)
        
    # search all columns for links
    def searchColumnsForLinks(self):
        for col in range(1, DIM+1):
            cells = self.board.getColumn(col)
            self.enterLinks(cells)
        
    # search all quadrants for links
    def searchQuadrantsForLinks(self):
        for d1 in range(1, dim+1):
            for d2 in range(1, dim+1):
                cells = self.board.getQuadrant(d1,d2)
                self.enterLinks(cells)
                
    # initial method             
    def provideAllLinks(self):
        # destroy all tables with strong, weak, inner links
        self.reinitialize()
        # search all regions for such links
        self.searchRowsForLinks()
        self.searchColumnsForLinks()
        self.searchQuadrantsForLinks()
        
    
    
        
        

        
    
                
    