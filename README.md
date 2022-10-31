# Sudoku Solver, Generator and Shell

Extensible Python code to generate and solve Sudoku puzzles
applicable to standard Sudoku board with 9 x 9 positions (= cells) and
digits in {1, 2, ..., 9}.

The dimension must form a square.

Standard board: dim = 3 and DIM = dim * dim = 9
consists of 3x3 quadrants each of which is a 3x3-matrix of
cells.

Goal: place numbers 1..DIM {1 .. 9} in each cell, so that after
every step the following rule holds:
there must be no identical numbers in any quadrant, row or 
column.
Game is over when all locations/cells on the board are occupied.

Internally, a Sudoku puzzle/board is considered in the following
way:

The 9x9-puzzle is structured into 3x3 quadrants that are numbered as (d1,d2) where d1 is the row and d2 is the column (d1,d2 in [1,3]).

|Q1,1|              |Q1,2|              |Q1,3| <- d1 = 1



|Q2,1|              |Q2,2|              |Q2,3| <- d1 = 2



|Q3,1|              |Q3,2|              |Q3,3| -> d1 = 3


^                   
|                   
d2 = 1              

    
    
    
          
 Example:
          
                           column
                            |
                            v
        1       2       3           4       5       6           7       8       9 <- column numbers                       
        =========================================================================
        0       2       3           6       1       0           0       0       0 <- row 1
                                                                        <-------- Quadrant 1,3
        1       0       4           3       0       5           2       0       0 <- row 2
 
        0       0       0           4       7       8           1       0       3 <- row 3   
                                                                ^
                                                                |--------------- position (3, 7)     
     
        7       0       0           0       0       0           0       0       0 -< row 4
                                ...
 
        4       5       0           1       3       0           0       0       0 <- row 9
 
 
  
0 means empty field

The data structure _data[] contains DIM x DIM = 81 cells of (x,y,z)-
tuples. _data[] is a unidirectional array respectively list.
To make this structure appear as a two-dimensional array
mapping functionality is provided. The user sees _data as
a two-dimensional array with indices going from 1 to 9.

Entries of _data[]-array:
   the array stores a tuples (x, y, z) for each position
   
    where:
            x is True  => location is occupied by number y
    
            x is false => location is vacant and ...
            
            ... z defines the numbers which influence this position, 
            i.e., numbers which can not occupy this position and are 
            therefore no candidates.
            
Short explanation of influencers and candidates:

An influencer is the number n of an occupied cell c in a region (the quadrant in which the cell lives, its col, its row).
As the occupied cell c "sees" all cells c' in its region, n cannot be set in these c' =>  n influences its region.
Thus, n is an influencer of c'. c' can never be occupied by n.

A candidate is a possible value an unoccupied cell c can have. 

If n is a candidate of cell c', it can't be an influencer.
If n is an influencer of cell c', it can't be a candidate.

=> all numbers = union(influencers of cell, candidates of cell) => both sets complement each other.

In the beginning of a Sudoku puzzle it is much easier to monitor the influencers. If more and more cells get occupied, it is easier to monitor the candidates as there often are only a few.
This implementations supports both influencers and candidates, but internally uses influencers (see addInfluencer()-methods).

    
The data structure _data[] contains DIM x DIM = 81 cells of (x,y,z)-
tuples. _data[] is a unidirectional array respectively list.
To make this structure appear as a two-dimensional array,
mapping functionality is provided. The user sees _data as
a two-dimensional array with indices going from 1 to 9 (if
DIM is 9). 

for example:
    self._data[self.map(i, j)] 
    represents the cell in 
    row i and column j with i,j in [1...9]
    
Instead of accessing the array in such a low-level way, it
is possible to use getters and setters,
for example,

    tuple = self.getElement(i,j) instead of self._data[self.map(i, j)] 
    
    self.setElement(i,j,tuple)   instead of self._data[self.map(i, j)] = tuple
    
    tuple = self.getElementInQuadrant(d1,d2,r,c) instead of
                  tuple = self._data[self.mapQuadrant(d1,d2,r,c)]


This Sudoko solver does not intend to calculate the solution
by brute-force, but by mimicking human players and their 
strategies. Nonetheless, it also provides a brute force method
solveBF() to get the solution in brute force fashion. Mainly,
brute force solvers are used to create new Sudoku puzzles
which is the purpose of the SudokoGenerator.

The included strategies are not sufficient for playing
the Sudoku game successfully, at least not when dealing
with more complex puzzles. 
Instead, SudokuSolver intends to be an experimentation 
platform where developers may plug-in additional strategies.

OccupationStrategies and InfluenceStrategies are used to extend 
SudokuSolver. 

OccupationStrategies help to find cells that can be occupied.
They are called within the method canBeOccupied() of
the SudokuSolver class. 

InfluenceStrategies help reduce the number of candidates 
for cells, thus assisting the occupation strategies. If 
e.g. a cell is influenced by {1,2,3,4,5,6,7}, the only
candidates left are 8 and 9. If by an influence strategy
8 can be ruled out as a candidate, 9 must be the valid
occupant of the cell.

Influence strategies are called within the method occupy() 
of the SudokuSolver class. Whenever a number becomes
occupant in one of the cells, an influence strategy
might figure out where to add influences respectively
where to rule out candidates.

Both types of strategies go in hand in hand for solving a puzzle.

There is a strategy called "Cheating" which is not really
a strategy. Instead it uses a solution that was calculated
in a brute force algorithm. Whenever occupy() does not find
a solution in another strategy, cheating does. To use
Cheating instantiate the SudokuSolver class with the
argument withCheating set to True.

To add your own occupation strategy: 

    Derive subclass from class OccupationStrategy. 
    
    Each applyXXXX()-method either returns 0, if 
    no solution was found for a given (i,j),       
    or the number to fill in otherwise.
    
    Extend __init__ of class SudokuSolver to instantiate 
    and register your own strategy. 
    
    Pass the used board as argument to constructor of 
    own strategy and ...
    
    ... assign it to self.board (Dependency Injection)
    
For examples see RemainingInfluencerStrategy and
DeepCheckStrategy in the code.

Example skeleton:

class MyStrategy(OccupationStrategy): # must be derived from Strategy
        def __init__(self, board):
            self.board = board
        
        def applyToQuadrant(self, i, j):
            # analye quadrant and return the number 
            # to be put in (i,j). If no number is found 
            # then 0 should be returned.
            # ... 
            return aNumber
                
        def applyToColumn(self, i,j):
            # analye column and return the number 
            # to be put in (i,j). If no number is found 
            # then 0 should be returned  
            # ... 
            return aNumber
                
        def applyToRow(self, i, j):
            # analye row and return the number 
            # to be put in (i,j). If no number is found 
            # then 0 should be returned  
            # ... 
            return aNumber
            
In addition, the OccupationStrategy class defines a method applyStrategy
all its children inherit. This method is used to call the 
apply()-methods for rows, columns, and quadrants. It basically
is collecting the results of the other methods:
    
        def applyStrategy(self, i, j):
            res = self.applyToQuadrant(i, j)
            if res != 0:
                return res
            res = self.applyToRow(i, j)
            if res != 0:
                return res
            res = self.applyToColumn(i, j)
            return res
            
You may override applyStrategy() in your own strategy class.
Likewise, you may implement only one or even none of the other 
methods such as applyToRow() so that it does only return 0, if you
do not need the method for your strategy:

    
    def applyToRow(self, i, j):
        return 0
        
   
You may also leave out such a method completely such as in:


   def applyToRow(self, i, j):
        pass
        

To add your own influence strategy, your strategy class must
have InfluenceStrategy as parent class:

    
    class MyInfluenceStrategy(InfluenceStrategy):
        def __init__(self, board):
            self.board = board 
            
        # may implement additional methods
            
        def applyStrategy(self):
            # search for possible elimination of candidates 
            # is not supposed to return a result
            


To add your own influence strategy: 

    Derive subclass from class InfluenceStrategy as described 
    above. 
    
    Implement the applyStrategy() method.
    
    Extend "__init__" of class SudokuSolver to instantiate 
    and register your own strategy. 
    
    Pass the used board as argument to constructor of 
    own strategy and ...
    
    ... assign it to self.board (Dependency Injection)
    
For examples see IndirectInfluencersStrategy, XWingStrategy,
and SwordfishStrategy in the code.

The method attachOccupationStrategy(self, strategy) of SudokuSolver is
used to register additional occupation strategies.

The method attachInfluenceStrategy(self, strategy) is used to register
additional influence strategies

SudokuSolver supports three formats:
    
    puzzle specified by a string
    
    puzzle specified programmatically
    
    puzzle specified as a CSV file (Excel format)

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
SudokuGenerator in combination. It provides a shell
for creating and solving Sudoku puzzles with 
handy runtime options such as inspecting current 
occupants, candidates, or influencers.

If SudokuSolver fails to solve a puzzle, it will display
the candidates for each remaining unoccupied cell. This
may be used to analyze whether and how the class should be
extended with additional strategies.

By using withCheating as argument to SudokuSolver, the solver might use cheating (= looking up a brute force solution).

By using withMonitoring the program will monitor all calls of addInfluencer() that is responsible to add influencers :=: remove candidates in cells.

Example how to use SudokuShell:

            SudokuShell().run(withCheating = False, withMonitoring = False)

Example how to use SudokuGenerator for creating a new puzzle:

            # create a new puzzle 
            board = generator.createSudoku(minimumOccupancy = 17)
            
Example how to let SudokuSolver solve the new puzzle:

            # turn the board into a string
            intarray = generator.turnIntoString(board)
            # turn  the intarray to an internal data structure
            # the solver understands
            solver.turnStringIntoBoard(intarray)
            # call the solver to solve the puzzle
            solver.solve(Info.PRETTY)
            
           
An additional SudokuWhatIf class helps try scenarios when the solver gets stuck. In this case, the user can enter her own guesses and then see what happens. If these guesses lead to an invalid state, the SudokuWhatIf implementation will return to the previous well known state from where other guesses are possible.

The class StatePersistence is a singleton that maintains states of the SudokuBoard. Users may leverage the commands b (= backup) and r (= restore) within SudokuSolver to save current states or restore them. Internally a dictionary is used for maintaining these states using user-defined names as keys. StatePersistence always creates deep copies of these states and returns deep copies of these states to ensure data protection. 

Classes like Chain and ColoredChain were introduced to allow implementation of chaining in the future.
           
           
The implementation has been partitioned into multiple files:

solver.py contains the SudokuSolver, the SudokuWhatif scenario class as well as one strategy class. Their responsibility is to solve a Sudoku puzzle using different strategies.

strategy.py implements the strategy base classes InfluenceStrategy and OccupationStrategy.

memory.py provides class StatePersistence which helps storing and restoring Sudoku puzzles in memory.

generator.py includes the SudokuGenerator class responsible for creating new puzzles.

chains.py is not yet used, but offers the classes Chain and ColoredChain for dealing with chaining strategies.

shell.py encapsulates the class SudokuShell.py as well as the main program. It illustrates how to facilitate the aforementioned classes.

whatif.py is responsible for letting the user experiment with What-if scenarios, should the solver not be able to solve a puzzle.

board.py comprises all functionality to manage and access the board storage.

___strategy.py: implementation of a single occupation or influence strategy.


To run the main programm start the shell:

        %python shell.py
            
     
