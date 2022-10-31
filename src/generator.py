"""
Distributed with:
GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
           
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

from     random  import shuffle
from     copy    import deepcopy

dim = 3          # size of Sudoku quadrants
DIM = dim * dim  # size of Sudoku puzzle

# make sure that dim and DIM have valid values
assert isinstance(dim, int), 'dim must be an integer'
assert isinstance(DIM, int), 'DIM must be an integer'
assert dim > 0, 'dim must be positive'
assert DIM > 0, 'DIM must be positive'
assert dim * dim == DIM, 'DIM must be dim * dim'


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
            board_copy = deepcopy(self.board)
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

