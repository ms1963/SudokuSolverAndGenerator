"""
Distributed with:
GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007


The class StatePersistence defines methods to persist and restore boards.
It is just a global dictionary implemented as a singleton.
It does not provide functionality to save data to a file or restore
data from a file. 
"""       

from copy import deepcopy
   
class StatePersistence:
    # no __init__ constructor needed
    _instance = None
    def __new__(cls):
        if cls._instance == None:
            cls._instance = super(StatePersistence, cls).__new__(cls)
            cls.states = {}
        return cls._instance
    
    def persistState(cls, name, data):
        cls.states[name] = deepcopy(data)
        
    def restoreState(cls, name):
        return deepcopy(cls.states[name])
        
    def keys(cls):
        return cls.states.keys()
        
    def items(cls):
        return cls.states.items()
        
    def len(cls):
        return len(cls.states)
        