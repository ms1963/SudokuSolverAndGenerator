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
This package consist of the  classes

    Chain, ColoredChain
    
    
The classes Color, Chain, ColoredChain are introduced to support
chaining strategies for SudokuSolver.
They allow chain nodes with x, y as key, and listOfInfluencers, 
Color as elements.            
#############################################################
"""

# Helper class for ColoredChain class 


from     enum    import Enum, unique

@unique
class Color(Enum):
    Black         = 0
    Red           = 1
    Blue          = 2
    Green         = 3
    Yellow        = 4
    LightBlue     = 5
    Orange        = 6
    Cyan          = 7
    Turquise      = 8
    Pink          = 9
    Purple        = 10
    LightGreen    = 11
    Grey          = 12
    Magenta       = 13
    White         = 42


"""
The class Chain implements chains of nodes (x,y,z) where x is the
x-coordinate, y is the y-coordinate, and z is the content. Both
x and y define the unique key for accessing data
"""
class Chain:   
    # init chain
    def __init__(self):
        self.chain  = []
        
    # appending an element to a chain
    def append(self, node):
        self.chain.append(node)
        
    # length of chain
    def len(self):
        return len(self.chain)
        
    # add a node
    def __add__(self, node):
        self.append(node)
        return self
        
    # an empty chain is closed
    # a chain with the same node at start and end is closed
    # all other chains are open
    def isClosed(self):
        return (self.len() <= 1) or ((self[0][0] == self[self.len()-1][0]) and (self[0][1] == self[self.len()-1][1]))
            
           
    # find first occurrence of (x,y) in chain
    # if found returns index, and -1 otherwise
    def find(self, x, y):
        result = -1
        for idx in range(0, self.len()):
            elem = self.chain[idx]            
            if (elem[0],elem[1]) == (x,y):
                result = idx 
                break
        return result
        
    def findAll(self, x, y):
        resultList = []
        for idx in range(0, self.len()):
            elem = self.chain[idx]            
            if (elem[0],elem[1]) == (x,y):
                resultList.append(idx) 
        return resultList
        
    # look for a particular candidate in the chain
    def findCandidateInChain(self, cand):
        resultList = []
        for elem in self:
            if cand in elem[2]:
                resultList.append((elem[0],elem[1]))
        return resultList
        
    # find in which nodes cands is included
    def findCandidatesInChain(self, cands):
        resultList = []
        for elem in self:
            if set(cands).intersection(set(elem[2])) == set(cands):
                resultList.append((x,y))
        return resultList
    
    # find all nodes with n candidates (bivalue cells)
    def findNCandidatesInChain(self, n):
        resultList = []
        for elem in self:
            if len(elem[2]) == n:
                resultList.append((elem[0],elem[1]))
        return resultList
    
    # find all nodes which have cands as their set of candidates
    def findExactCandidatesInChain(self, cands):
        resultList = []
        for elem in self:
            if set(elem[2]) == set(cands):
                resultList.append((elem[0],elem[1]))
        return resultList
                        
    # get index of node with coordinates (coord[0], coord[1])
    def __indexof__(self, coord):
        (x,y) = coord
        return self.find(coord[0],coord[1])
        
    # c[i]
    def __getitem__(self, i):
        if i < 0 or i >= self.len():
            raise ValueError("index out of range")
        return self.chain[i]
        
    # get influencer List at index i
    def getListAt(self, i):
        if not i in range(0, self.len()):
            raise ValueError("index out of range")
        elem = self[i]
        return elem[2]
        
        
    # c[i] = node
    def __setitem__(self, i, node):
        if i < 0 or i >= self.len():
            raise ValueError("index out of range")
        self.chain[i] = node
               
    # removal of a node: removes tthe first node found
    def remove(self, x, y):
        found = False
        for node in self:
            if (node[0], node[1]) == (xn, yn): 
                self.chain.remove(node)
                found = True
                break
        if not found:
            raise ValueError("object not in chain")
            
    # remove all nodes woth (x,y)-coordinates
    def removeAll(self, x, y):
        for node in self:
            if (node[0], node[1]) == (xn, yn): 
                self.chain.remove(node)
        
    # check for empty chain
    def isEmpty(self):
        return self.len() == 0
        
    # string representation of content
    def __str__(self):
        result = ""
        for idx in range(0, len(self.chain)):
            (x,y,content) = self.chain[idx]
            result += "(" + str(x) + "," + str(y) + "," + str(content) + ")\n"
        return result
        
    # string representation of object
    def __repr__(self):
        result = "Chain() with length " + str(self.len())
        return result
    
    # building a generator/iterator    
    def __iter__(self):
        for idx in range(0, self.len()):
            yield self.chain[idx]
            
    # check for availability of node with coord as coordinates
    def __contains__(self, coord):
        return self.find(coord[0],coord[1]) != -1
        
    # check for equality
    def __eq__(self, other):
        if not isinstance(other, Chain): return False
        if self.len() != other.len(): return False
        for i in range(0, self.len()):
            (x1,y1,z1) = self[i]
            (x2,y2,z2) = other[i]
            if (x1 != x2) or (y1 != y2) or (set(z1) != set(z2)): return False
        return True
    
    # apply functionality of predicate to all chein elements
    # predicate expects list
    def apply(self, predicate):
        resultList = []
        for idx in range(0, self.len()):
            (x,y,z) = (self[idx][0], self[idx][1], self[idx][2])
            retv = predicate(z)
            resultList.append((idx, retv))
        return resultList
        



"""
In class ColoredChain nodes get an additional color code to support
coloring algorithms. ColoredChain is a subclass of Chain.
A ColoredChain node contains nodes like (x,y,z,c) where x is the
x-coordinate, y is the y-coordinate, z is the content, and c is the
color code

"""
       
class ColoredChain(Chain):
    # init chain
    def __init__(self):
        super().__init__()
        
    def createColoredSubchain(self, color):
        cc = ColoredChain()
        for elem in self:
            (x,y,z,c) = elem
            if c == color:
                cc.append(elem)
        return cc
        
    def getColorAt(self, i):
        if not i in range(0, self.len()):
            raise ValueError("index out of range")
        (x,y,z,c) = self[i]
        return c
        
    # string representation of content
    def __str__(self):
        result = ""
        for idx in range(0, len(self.chain)):
            (x,y,content, c) = self.chain[idx]
            result += "(" + str(x) + "," + str(y) + ", color = " + repr(c) + "," + str(content) + ")\n"
        return result
        
    # string representation of object
    def __repr__(self):
        result = "ColoredChain() with length " + str(self.len())
        return result
    
    def __eq__(self, other):
        if not isinstance(other, ColoredChain): 
            return False
        if self.len() != other.len(): 
            return False
        for i in range(0, self.len()):
            (x1,y1,z1,c1) = self[i]
            (x2,y2,z2,c2) = other[i]
            if (x1 != x2) or (y1 != y2) or (c1 != c2) or (set(z1) != set(z2)): 
                return False
        return True
    
    # apply functionality of predicate to all chain elements
    # predicate expects color plus list
    def apply2(self, predicate):
        resultList = []
        for idx in range(0, self.len()):
            (x,y,z,c) = (self[idx][0], self[idx][1], self[idx][2], self[idx][3])
            retv = predicate(c, z)
            resultList.append((idx, retv))
        return resultList
        