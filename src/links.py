
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
    
    For strong and weak links (strongLinks, weakLinks
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
        
    For weak link this implies: 
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




from     board             import Board, DIM, dim

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
        
    
    
        