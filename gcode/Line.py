# -*- coding: utf-8 -*-
import numpy as np

from .GCode import GCode

a = 10  # [mm]. Shorest leg of the triangle will be 10 mm, 1 cm, 0.01 m long.
default_feed = 300  # mm/min. 4 mm/s.
default_power = 1  # [dimensionless]


def hline(X0=0, Xf=10, Y=0, n_points=2):
    p = np.linspace(X0, Xf, n_points, endpoint=True)
    line_points = np.array([p, Y * np.ones(p.shape)])
    return line_points.transpose()


def vline(X=0, Y0=0, Yf=10, n_points=2):
    p = np.linspace(Y0, Yf, n_points, endpoint=True)
    line_points = np.array([X * np.ones(p.shape), p])
    return line_points.transpose()


class Line(GCode):
    def __init__(
        self,
        points=hline(X0=0, Xf=10, Y=0),
        feed=default_feed,
        power=default_power,
        dynamic_power=True,
        *args,
        **kwargs,
    ):
        self.points = points.squeeze()
        self.feed = feed
        self.power = power
        self.dynamic_power = dynamic_power
        super().__init__(*args, **kwargs)

        self.generate_gcode()

    def reverse(self):
        # Reverse each of the points.
        flip_n_reverseit = np.eye(self.points.shape[0])[:, ::-1]
        self.points = np.matmul(flip_n_reverseit, self.points)

    @property
    def X(self):
        # X Points in Line
        return self.points[:, 0]

    @property
    def Y(self):
        # Y Points in Line
        return self.points[:, 1]

    @property
    def x_0(self):
        # X[0], first X point
        return self.points[0, 0]

    @property
    def y_0(self):
        # Y[0], first Y point
        return self.points[0, 1]

    @property
    def x_f(self):
        # X[-1], final X point.
        return self.points[-1, 0]

    @property
    def y_f(self):
        # Y[-1], final Y point.
        return self.points[-1, 1]

    def __repr__(self):
        return "Line<len={}mm, feed={}, power={}>".format(
            self.dist, self.feed, self.power
        )

    @property
    def dists(self):
        """ Distances traveled in each line segment """
        # For remaining points.
        dist_ = list()
        # Look through each of the points in the shape.
        for idx in range(1, self.points.shape[0]):
            # Determine how far moved X & Y
            dX = self.points[idx][0] - self.points[idx - 1][0]
            dY = self.points[idx][1] - self.points[idx - 1][1]
            d = np.sqrt(np.power(dX, 2) + np.power(dY, 2))
            dist_.append(d)
        return dist_

    @property
    def dist(self):
        """ Total distance traveled. """
        """ Return the distance traveled """
        return np.round(np.sum(self.dists), 5)

    @property
    def times(self):
        """ Amount of time spent drawing each line spegment.

        Does not take into consideration acceleration curves """
        rate = self.feed / 60  # [mm/s]
        return [dist / rate for dist in self.dists]

    @property
    def time(self):
        """ Total distance traveled. """
        return np.round(np.sum(self.times), 5)

    def generate_gcode(self):
        self.buffer = list()
        # Move to start of the line.
        self.G0(X=self.points[0, 0], Y=self.points[0, 1])

        # Set power.
        if self.dynamic_power:
            self.M4(S=self.power)
        else:
            self.M3(S=self.power)

        # For remaining points.
        for row_idx in range(1, self.points.shape[0]):
            self.G1(X=self.points[row_idx, 0], Y=self.points[row_idx, 1], F=self.feed)
        self.M5()

    @property
    def g(self):
        self.generate_gcode()
        return "\n".join(self.buffer)
