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
from     enum              import Enum, unique
from     random            import shuffle
from     copy              import copy, deepcopy
import   os.path
from     memory            import StatePersistence
from     chains            import Chain
from     generator         import SudokuGenerator
from     strategy          import OccupationStrategy, InfluenceStrategy
from     board             import Board, DIM, dim, Links
from pointingstrategy      import PointingPairsAndTriplesStrategy
from remainingstrategy     import RemainingInfluencerStrategy
from deepcheckstrategy     import DeepCheckStrategy
from oneleftstrategy       import OneCandidateLeftStrategy
from indirectinflstrategy  import IndirectInfluencersStrategy
from xwingstrategy         import XWingStrategy
from swordfishstrategy     import SwordFishStrategy
from hiddenpairsstrategy   import HiddenPairsStrategy
from hiddentriplesstrategy import HiddenTriplesStrategy
from cheatstrategy         import Cheating




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
        
        strategy = DeepCheckStrategy(self.board)
        self.attachOccupationStrategy(strategy)
        strategy = OneCandidateLeftStrategy(self.board)
        self.attachOccupationStrategy(strategy)
        strategy = RemainingInfluencerStrategy(self.board)
        self.attachOccupationStrategy(strategy)
       
        if self.withCheating:
            strategy = Cheating(self.board)
            self.attachOccupationStrategy(strategy)
        
        # influence strategies
        strategy = XWingStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        strategy = SwordFishStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        strategy = HiddenPairsStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        strategy = HiddenTriplesStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        strategy = PointingPairsAndTriplesStrategy(self.board)
        self.attachInfluenceStrategy(strategy)
        strategy = IndirectInfluencersStrategy(self.board)
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
    # set surpress to True to prevent information about
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
        print("        ' 4 5 6 '    specify the influencers or candidates.")
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
                # before strategies are used, strong, weak and inner links
                # are created
                # create weak, strong, inner links for strategies
                # that use chaining strategies. Links must be recalculated
                # in each iteration. For performance reasons, it should not
                # be called after each occupy()
                self.board.createLinks()
                if self.monitoringActive:
                    print("Strong, inner, and weak links created")
                for j in range(1, DIM+1):   # cells and find a cell that 
                                            # can be occupied
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
                                case "p":
                                    print("Saving state to Persistence")
                                    while True:
                                        name = input(" Specify name ---> ")
                                        if name != "" and not name in StatePersistence().keys():
                                            StatePersistence().persistState(name, self.board._data)
                                            break
                                case "w":
                                    repeat = 0
                                    rows = self.board.turnBoardIntoList()
                                    while True and repeat < 3:
                                        fname = input("* Enter name of output file: ")   
                                        if os.path.isfile(fname):
                                            print("  Error - file already exists. Use another filename.")
                                        elif len(fname) == 0:
                                            print("  Error: Incorrect file name")
                                            repeat += 1
                                        else:
                                            self.board.writeSudokuToCSV(fname, rows)    
                                            print("Output File " + fname + " written !")
                                            break
                                    if repeat == 3:
                                        print("Action stopped")
                                    input("press any key to continue ")                       
                                case "h":
                                    print("""
        ***** Help *****
        press     h for help
                  s for shuffling strategies
                  n for noninteractive mode
                  a for activating Monitoring
                  d for deactivating Monitoring
                  p to  persist state in stack
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
