
"""
Distributed with:
GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
""" 

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

from solver import SudokuSolver, Info, SudokuWhatIf
from generator import SudokuGenerator
from memory import StatePersistence
import os.path

class SudokuShell:
    # no __init__ constructor needed
    _instance = None
    def __new__(cls):
        if cls._instance == None:
            cls._instance = super(SudokuShell, cls).__new__(cls)
        return cls._instance
        
    # the withCheating argument determines in run() to use 
    # cheating in the solver 
    # the withMonitoring argument determines in run() to use 
    # monitoring of addInfluencer()-calls in the solver
    def run(cls, withCheating = False, withMonitoring = False):
        strategiesAlreadyDisplayed = False
        while True:
             # instantiate a new solver
            solver = SudokuSolver(withCheating, withMonitoring)
            print("(SudokuShell): Enter rd to read an existing CSV file, r to restore a board, q to quit, or other key to start new Sudoku")
            value = input(" ---> ")
            print()
            normalMode = False
            match value:
                case "q":
                    print("Exiting from SudokuShell ...")
                    break
                case "rd":
                    completed = False
                    while not completed:
                        fname = input("* Enter name of input file: ")   
                        if not os.path.isfile(fname):
                            print("  Error - file not found.")               
                        else:
                            rows = solver.readSudokuFromCSV(fname)
                            completed = True
                            # adapt the result for the SudokuSolver
                            solver.turnListIntoBoard(rows)
                case "r":
                        if StatePersistence().len() == 0: 
                            print("No state stored")
                            print()
                            continue
                        else:
                            print("Enter key of state to restore")
                            for key, value in StatePersistence().items():
                                print(" - '" + str(key) + "'")

                            completed = False
                            while not completed:
                                answer = input(" --> ")
                                completed = answer in StatePersistence().keys()
                                if (completed):
                                    solver._data = StatePersistence().restoreState(answer)
                                else:
                                    print("Invalid key")
                            solver.steps = 0
                            print("State restored")
                            print()                           
                case other:
                    normalMode = True
                        
            if not strategiesAlreadyDisplayed and withMonitoring:
                print("Identifying installed strategies ...")
                print()
                print("Occupation Strategies:")
                for strategy in solver.getInstalledOccupationStrategies():
                    print(type(strategy).__name__)
                print()
                print("Influence Strategies:")
                for strategy in solver.getInstalledInfluenceStrategies():
                    print(type(strategy).__name__)
                print()
                strategiesAlreadyDisplayed = True
            if normalMode:
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
            succeeded = solver.solve(Info.PRETTY)
            if succeeded:
                print("SudokuSolver succeeded solving the puzzle!")
            else:
                print("SudokuSolver failed solving the puzzle!")
                completed = False
                while not completed:
                    wrongAnswer = True
                    while wrongAnswer:
                        print()
                        wish = input("Wanna try a What-If scenario (y,n)? ")
                        if wish == "y":
                            wrongAnswer = False
                            swi = SudokuWhatIf(solver)
                            result = swi.runScenario()
                            if result:
                                print("Your guess was right")
                            else: 
                                print("Scenario did not work out")
                            completed = result
                        elif wish == "n":
                            wrongAnswer = False
                            completed = True
                            break
                        else:
                            print("Please, answer y or n!")
                            
SudokuShell().run(withMonitoring = False, withCheating = False)
                            


                        