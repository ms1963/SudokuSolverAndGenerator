# Sudoku Solver and Generator

Extensible Python code to generate and solve Sudoku puzzles
applicable to standard Sudoku board with 9 x 9 positions and
digits in {1,2, ..., 9}
The dimension must be a quadratic.
Standard board: dim = 3 and DIM = dim * dim = 9
consists of 3x3 quadrants each of which is a 3x3-matrix of
numbers.
Goal: place numbers 1..DIM {1 .. 9} in each quadrant, so that after
every step the following rule holds:
there must be no identical numbers in any quadrant, row or 
column.
Game is over when all locations on the board are occupied.

Internally, a Sudoku puzzle/board is considered in the following
way:

The 9x9-puzzle is structured into 3x3 quadrants.

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
        0       2       3           6       1       0           0       0       0
                                                                        <-------- Quadrant 1,3
        1       0       4           3       0       5           2       0       0
 
        0       0       0           4       7       8           1       0       3    
                                                                ^
                                                                |--------------- position (3, 7)     
     
        7       0       0           0       0       0           0       0       0
                                ...
 
        4       5       0           1       3       0           0       0       0 <- row 9
 
 
  
0 means empty field

The data structure _data[] contains DIM x DIM = 81 cells of (x,y,z)-
tuples. _data[] is a unidirectional array respectively list.
The make this structure appear as a two-dimensional array
mapping functionality is provided. The user sees _data as
a two-dimensional array with indices going from 1 to 9.

Entries of _data[]-array:
   the array stores a tuples (x, y, z) for each position
    where x is True  => location is occupied by number y
          x is false => location is vacant and ...
          ... z defines the numbers which influence this position, 
          i.e., numbers which can not occupy this position and are 
          therefore no candidates.
    
The data structure _data[] contains DIM x DIM = 81 cells of (x,y,z)-
tuples. _data[] is a unidirectional array respectively list.
The make this structure appear as a two-dimensional array
mapping functionality is provided. The user sees _data as
a two-dimensional array with indices going from 1 to 9 (if
DIM is 9). 

for example:
    self._data[self.map(i, j)] 
    represents the cell in 
    row i and column j with 1 <= i,j <= 9
    
Instead of accessing the array in such a low-level way it
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

What are influencers and what are candidates?
An influencer is a number that cannot occupy a cell. In the 
example above, the 5 in the last row (9, 2) is an influencer
for all other locations in the same row, column or quadrant.
This implies: 5 can not be an occupant of these other locations.
Candidates of a cell are numbers that may occupy this cell.
If a number is a candidate, it can not be an influencer 
ánd vice-versa.

OccupationStrategies help to find cells that can be occupied.
They are called within the method canBeOccupied() of
the SudokuSolver class. 

InfluenceStrategies help reduce the number of candidates 
for cells, thus assisting the occupation strategies. If 
e.g. a cell is influenced by {1,2,3,4,5,6,7} the only
candidates left are 8 and 9. If by an influence strategy
8 can be ruled out as a candidate, 9 must be the valid
occupant of the cell.
Influence strategies are called within the method occupy() 
of the SudokuSolver class. Whenever a number becomes
occupant in one of the cells, an influence strategy
might figure out where to add influences respectively
where to rule out candidates.

Both types of strategies go in hand in hand for solving a puzzle.

There is an strategy called "Cheating" which is not really
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
Likewise, you may implement only one of the other methods
such as applyToRow() so that it does only return 0, if you
do not need the method for your strategy:
    
    def applyToRow(self, i, j):
        return 0
        

    
To add your own influence strategy, your strategy class must
have InfluenceStrategy as parent class:
    
    class MyInfluenceStrategy(InfluenceStrategy):
        
        def __init__(self, board):
            self.board = board 
            
        # may implement additional methods
            
        def applyStrategy(self):
            # search for possible elimination of candidates 
            # is not supposed to return a result
            
The method attachOccupationStrategy(self, strategy) of SudokuSolver is
used to register additional occupation strategies.
The method attachInfluenceStrategy(self, strategy) is used to register
additional influence strategies

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

SudokuSolver supports three formats:
    
    puzzle specified by a string
    
    puzzle specified programmatically
    
    puzzle specified as a CSV file (Excel format)

=============================================================
This program consist of the three core classes:

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
may be used to figure out whether the class should be
extended with additional strategies.
