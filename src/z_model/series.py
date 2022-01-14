from numpy import empty, random, sqrt


class Series:
    '''
    The forecast model is of the form:

    .. math::
        dx = m1 (\theta - x) dt + m2 dx + \sigma dw

    where:

    * ``m1`` is the mean reversion parameter,
    * ``theta`` is the long run average,
    * ``m2`` is the momentum parameter,
    * ``sigma`` is the volatility, and
    * ``dw`` is a Brownian motion.
    '''
    def __init__(self, T: float, N: int, x0: float = None, dx0:float=.0, theta:float=.0, m1:float=.0, m2:float=.0, sigma:float=.0, m:int=1, fun=lambda x: x):
        '''

        :param NAME: str - The name of the macroeconomic variable that should be generated. It should match
            (case sensitive) references in other inputs.

        :param START_DATE: datetime - From when should the macroeconomic forecast start. This should correspond to the
            value of ``x0`` below.

        :param T: float - The number of periods to forcast. Note that if the model was calibrated on quaterly data,
            this would be the number of quarters to forecast.

        :param N: int - The length of the output vector. If the model was calibrated on quaterly data and the model
            requires a monthly output vector for the ECL calculations ``N`` would be ``3*T``.

        :param x0: float - The value of the series at the ``START_DATE``.

        :param dx0: float - The value of the first difference at the ``START_DATE``, i.e. x(t=0) - x(t=-1).

        :param theta: float - The Theta parameter in the model. The ``theta`` is the Central Tendency value.

        :param m1: float - The m1 (mean reversion) parameter in the model.

        :param m2: float - The m2 (momentum) parameter in the model.

        :param sigma: float - The models volatility parameter. Set equal to 0 if a deterministic forecast should
            be created.

        :param m: int - The number of simulations to create.

        :param fun: lambda - A transformation to apply to x after the forecast is created. Only ``EXPONENTIAL`` is
            supported at the moment and can be used to convert a variable that was modelled in the Log space to
            the nominal space.

        '''
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
