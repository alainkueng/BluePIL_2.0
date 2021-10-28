import numpy as np
from math import *
from scipy.optimize import root


class BpQuadlateration:
    pos_A1 = (0, 0)
    pos_A2 = (0, 0)
    pos_A3 = (0, 0)
    pos_A4 = (0, 0)

    n = 0

    def __init__(self, p_A1, p_A2, p_A3, p_A4, n):
        self.pos_A1 = p_A1
        self.pos_A2 = p_A2
        self.pos_A3 = p_A3
        self.pos_A4 = p_A4
        self.n = n

    def get_func(self, p, rssi):
        p_x = p[0]
        p_y = p[1]

        def f(x):
            return (x[0] - p_x)**2 + (x[1] - p_y)**2 - 10**((x[2] - rssi) / (5 * self.n))

        def df(x):
            return [2*(x[0] - p_x), 2*(x[1] - p_y), (-log(10) / (5 * self.n)) * 10**((x[2] - rssi) / (5 * self.n))]

        return f, df

    def avgtuple4(self, p1, p2, p3, p4, idx):
        return (p1[idx] + p2[idx] + p3[idx] + p4[idx]) / 4

    def quadlaterate(self, rssi1, rssi2, rssi3, rssi4):
        f1, df1 = self.get_func(self.pos_A1, rssi1)
        f2, df2 = self.get_func(self.pos_A2, rssi2)
        f3, df3 = self.get_func(self.pos_A3, rssi3)
        f4, df4 = self.get_func(self.pos_A4, rssi4)

        def func(x):
            f = [f1(x), f2(x), f3(x), f4(x)]
            df = [df1(x), df2(x), df3(x), df4(x)]
            return f, df

        centroidx = self.avgtuple4(self.pos_A1, self.pos_A2, self.pos_A3, self.pos_A4, 0)
        centroidy = self.avgtuple4(self.pos_A1, self.pos_A2, self.pos_A3, self.pos_A4, 1)
        sol = root(func, np.array([centroidx, centroidy, -30]), jac=True, method='lm')
        return sol



