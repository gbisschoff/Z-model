from pylab import plot, show, xlabel, ylabel, axhline
from numpy import empty, random, sqrt, linspace


class Series:
    def __init__(self, T: float, N: int, x0: float = None, dx0=.0, theta=.0, m1=.0, m2=.0, sigma=.0, m=1, fun=lambda x: x):
        self.T = T
        self.N = N
        self.x0 = theta if x0 is None else x0
        self.dx0 = dx0
        self.theta = theta
        self.m1 = m1
        self.m2 = m2
        self.sigma = sigma
        self.m = m
        self.fun = fun
        self.dt = T / N
        self.dx, self.x, self.fx = self._forecast()

    def __getitem__(self, item):
        return self.__dict__[item]

    def _forecast(self):
        x = empty((self.m, self.N+1)); x[:, 0] = self.x0
        dx = empty((self.m, self.N+1)); dx[:, 0] = self.dx0
        dw = random.normal(scale=sqrt(self.dt), size=(self.m, self.N))

        for i in range(self.N):
            dx[:, i+1] = self.m1 * (self.theta-x[:, i]) * self.dt + self.m2 * dx[:, i] + self.sigma * dw[:, i]
            x[:, i + 1] = x[:, i] + dx[:, i+1]

        return dx, x, self.fun(x)

    def plot(self, item: str = 'fx'):
        x = self[item]
        t = linspace(0.0, self.T, self.N + 1)
        for k in range(self.m):
            plot(t, x[k])
        axhline(y=self.fun(self.theta), color='black', ls='--')
        xlabel('t', fontsize=16)
        ylabel(item, fontsize=16)
        show()
