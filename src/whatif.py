"""
Distributed with:
GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
 
SudokuWhatIf is used to run what-if-scenarios if SudokuSolver does not succeed.
Users can specify guesses for cells and these scenarios will then be tested.
Note that this functionality is currently very expermimental.
"""

# Token values: helper class for CellAssignmentParser

from enum import Enum, unique
from solver import SudokuSolver, DIM, dim, Info
from copy import deepcopy

@unique
class Tokens(Enum):
    OPAREN = 10 # = [
    CPAREN = 11 # = ]
    ASSIGN = 12 # = =
    ERROR  = 13 
    EOF    = 14
    SEP    = 15 # = ,
    
    
class SudokuWhatIf:
    def __init__(self, solver):
        self.solver = deepcopy(solver)
        
    # parser for checking cell assigments the user types in such as [7, 9] = 6
    class CellAssignmentParser:
        def __init__(self, string):
            self.string = string
            self.pos = 0

        def getNextToken(self): # the lexer
            if self.pos >= len(self.string):
                print("Error: unexpected EOF")
                return Tokens.EOF
            while self.string[self.pos] == " " and self.pos < len(self.string)-1: 
                self.pos += 1
                continue 
            if self.string[self.pos] == '[': 
                self.pos += 1
                return Tokens.OPAREN
            elif self.string[self.pos] == "(": 
                self.pos += 1
                return Tokens.OPAREN
            elif self.string[self.pos] in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                self.pos += 1
                return int(self.string[self.pos-1])
            elif self.string[self.pos] == "]":
                self.pos += 1                 
                return Tokens.CPAREN
            elif self.string[self.pos] == ")": 
                self.pos += 1
                return Tokens.CPAREN
            elif self.string[self.pos] == ',': 
                self.pos+= 1
                return Tokens.SEP
            elif self.string[self.pos] == "=": 
                self.pos += 1
                return Tokens.ASSIGN
            elif self.string[self.pos] == "\n":
                return Tokens.EOF
            else: return Tokens.ERROR

        def parse(self): # recursive descent parser for user input
            num1 = 0
            num2 = 0
            num3 = 0
            # parse for [
            token = self.getNextToken()
            if token != Tokens.OPAREN:
                print("Error: [ or ( expected in pos " + str(1+self.pos))
                return None
            # parse for number in [1..9]
            token = self.getNextToken()
            if not token in range(1,10):
                print("Error: number in [1..9] expected in pos " + str(1+self.pos))
                return None
            else:
                num1 = token # row of cell
            # parse for ,
            token = self.getNextToken()
            if not token == Tokens.SEP:
                print("Error: , expected in pos " + str(1+self.pos))
                return None
            # parse for number in [1..9]
            token = self.getNextToken()
            if not token in range(1,10):
                print("Error: number in [1..9] expected in pos " + str(1+self.pos))
                return None
            else:
                num2 = token # col of cell
            # parse for ]
            token = self.getNextToken()
            if token != Tokens.CPAREN:
                print("Error: ] or ) expected in pos " + str(1+self.pos))
                return None
            # parse for =
            token = self.getNextToken()
            if not token == Tokens.ASSIGN:
                print("Error: = expected in pos " + str(1+self.pos))
                return None
            # parse for number in [1..9]
            token = self.getNextToken()
            if not token in range(1,10):
                print("Error: number in [1..9] expected in pos " + str(1+self.pos))
                return None
            else:
                num3 = token # value assigned to cell
                return (num1, num2, num3) # reflecting the input "[num1, num2] = num3""

    # run a what-if scenario
    def runScenario(self):
        self.board = deepcopy(self.solver.board)
        # create a new scenarioSolver with an existing solver as input
        scenarioSolver = SudokuSolver(withCheating = False, withMonitoring = True)
        self.solver.board = self.board
        for row in range(1, DIM+1):
            for col in range(1, DIM+1):
                (x,y,z) = self.solver.board.getElement(row, col)
                if x:
                    scenarioSolver.occupy(y, row, col)
        # display Sudoku board to run scenarios on
        self.solver.prettyPrint(self.solver.convertToIntArray())
        self.solver.printCandidatesAndInfluencers(candidates = True, title="LIST OF CANDIDATES")

        ready = False
        while not ready: # loop until preconditions for scenario hold
            correct = False
            print("(SudokuWhatIf): Please, make a guess for a cell (format: [r,c] = number, e.g., [3,7]=8) ")
            while not correct: # loop until the input is correct
                string = input(" ---> ")
                parser = self.CellAssignmentParser(string)
                # call parser
                result = parser.parse()
                # when parser could recognize correct input, stop loop
                if result != None: correct = True
            # check if cell is occupied
            isVacant = not scenarioSolver.isOccupied(result[0], result[1])
            containsCandidate = result[2] in scenarioSolver.board.getCandidates(result[0], result[1])
            if isVacant and containsCandidate:
                scenarioSolver.occupy(result[2], result[0], result[1])
                ready = True
                # check whether board is conformant
                if scenarioSolver.board.checkConformanceOfBoard() == False:
                    print("(SudokuWhatIf): Warning: this leads to an invalid board configuration.")
                    print("(SudokuWhatIf): Going back to start context.")
                    scenarioSolver = deepcopy(self.solver)
                    ready = False       
            else:
                if not isVacant:
                    print("(SudokuWhatIf): Cell [" + str(result[0]) + "," + str(result[1]) + "] already occupied")
                else: # containsCandidate == False
                    print("(SudokuWhatIf): Number " + str(result[2]) + " is not a candidate of cell [" + str(result[0]) + "," + str(result[1]) + "]")
        # solve scenario and return result
        return scenarioSolver.solve(info=Info.PRETTY)
                    
