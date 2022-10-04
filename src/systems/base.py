import numpy as np
import gym


class SystemEnv(gym.Env):


    def __init__(
        self, system, q=1, dt=1e-2, seed=None, constrained_actions=None,
        dtype=np.float32
    ):
        super().__init__()
        self.system = system
        self.dtype = dtype
        self.q = np.atleast_2d(q)
        self.dt = dt
        self.x = None
        self.dxdt = 0
        self.n = 0
        self.random = np.random.RandomState(seed)


    @property
    def state(self) -> np.ndarray:
        return self.x
    @state.setter
    def state(self, x: np.ndarray):
        self.x = np.asarray(x, dtype=self.dtype)


    def reset(self, x=None):
        self.x = (np.asarray(x) if x is not None else \
                  self.observation_space.sample()
                 ).astype(self.dtype)
        self.n = 0
        self.dxdt = 0
        return self.x


    def reward(self, xold, u, x):
        # squeeze in case x has a batch dimension [1, x] (while using torch.mpc)
        x = np.atleast_1d(x.squeeze())
        return -(x.T @ self.q @ x).item()


    def step(self, u: np.ndarray, from_x: np.ndarray=None, persist=True):
        u = np.asarray(u, dtype=self.dtype)
        old_dxdt = self.dxdt
        old_x = np.asarray(self.x if from_x is None else from_x, dtype=self.dtype)
        new_dxdt = self.system.dynamics(None, old_x, u)
        new_x = (old_x + 0.5 * (old_dxdt + new_dxdt) * self.dt).astype(self.dtype)
        r = self.reward(old_x, u, new_x)
        if persist:
            self.n += 1
            self.x = new_x
            self.dxdt = new_dxdt
        return new_x, r, False, {'u': u, 'dxdt': new_dxdt}
