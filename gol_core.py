import numpy as np
from numpy.lib.stride_tricks import as_strided

ruleOfLifeAlive = np.array([0, 0, 1, 1, 0, 0, 0, 0, 0])
ruleOfLifeDead = np.array([0, 0, 0, 1, 0, 0, 0, 0, 0])

def grid_nD(arr):
    assert all(_len>2 for _len in arr.shape)
    
    nDims = len(arr.shape)
    newShape = [_len-2 for _len in arr.shape]
    newShape.extend([3] * nDims)
    
    newStrides = arr.strides + arr.strides
    return as_strided(arr, shape=newShape, strides=newStrides)

class GameOfLife():
    def __init__(self, size=(10,10)):
        full_size = tuple(i+2 for i in size)
        self.full = np.random.choice([0, 1], size=full_size)
        nd_slice = (slice(1, -1),) * len(size)
        self.board = self.full[nd_slice]
        self.ndims = len(self.board.shape)
        
    def run_board(self, N_ITERS = 1):
        for _ in range(N_ITERS):
            neighborhoods = grid_nD(self.full)
            sumOver = tuple(-(i+1) for i in range(self.ndims))
            neighborCt = np.sum(neighborhoods, sumOver) - self.board
            self.board[:] = np.where(self.board, 
                                     ruleOfLifeAlive[neighborCt], 
                                     ruleOfLifeDead[neighborCt])
