from filterpy.common import Q_discrete_white_noise
from filterpy.kalman import KalmanFilter
import numpy as np


class BpKalman:

    __kf = KalmanFilter(dim_x=4, dim_z=2)

    def __init__(self, initial_x):

        self.__kf.x = initial_x

        self.__kf.H = np.array([[1, 0, 0, 0],
                                [0, 0, 1, 0]])

        self.__kf.P *= 0.5

        self.__kf.R = np.array([[0.3, 0],
                                [0, 0.3]])

    def predict_update(self, x, y, dt):

        self.__kf.Q = Q_discrete_white_noise(2, dt, block_size=2, var=0.001)

        # TODO: it would be good to also include some maximum movement here
        self.__kf.F = np.eye(4) + np.array([[0, 1, 0, 0],
                                            [0, 0, 0, 0],
                                            [0, 0, 0, 1],
                                            [0, 0, 0, 0]]) * dt
        self.__kf.predict()
        self.__kf.update(np.array([x, y]))
        return self.__kf.x