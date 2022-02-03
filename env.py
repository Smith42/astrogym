import gym
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle


plt.rcParams["toolbar"] = "None"


class AstroGymEnv(gym.Env):
    """
    OpenAI Gym-compatible environment for exploring astronomical images.
    """

    render_size = 500 # In pixels
    min_window_size = 100 # In pixels; CV2 will interpolate if this is < render_size
    plt_window_size = (6, 6) # In inches

    def __init__(self, img, do_render=False):
        self.observation_space = None
        self.action_space = gym.spaces.Box(np.float32(-1), np.float32(1), shape=(3,)) 
        ext = img.split(".")[-1]
        if ext == "jpg": self.img = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB)
        elif ext == "npy": self.img = np.load(img)[:,:,:3] # NOTE: What are the other two channels?
        self.img_size = self.img.shape[0]
        assert self.img_size == self.img.shape[1], "Image must be square"
        assert self.img_size >= 4 * self.render_size, "Insufficient image size" # NOTE: This is completely arbitrary
        self.do_render = do_render
        if self.do_render: 
            self.fig, self.ax = plt.subplots(figsize=self.plt_window_size)
            self.fig.canvas.manager.set_window_title("AstroGym")
            self.ax.set_xticks([]); self.ax.set_yticks([]); plt.ion(); self.ax.set_aspect("equal", "box")
            self.ax.margins(x=0, y=0)
            plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)            
            self._img_plt = self.ax.imshow([[0]], extent=(-1,1,1,-1))
            self._action_indicator = (
                Circle(xy=(0, 0), radius=0.05, facecolor="w", alpha=0.5),
                Rectangle(xy=(0, 0), width=2, height=2, edgecolor="w", fill=False)
                )
            for element in self._action_indicator: self.ax.add_artist(element)

    def reset(self):
        self._state = (0, self.img_size, 0, self.img_size)
        self._obs = self.obs()
        return self._obs 
    
    def step(self, action):
        assert action in self.action_space
        self._action = action
        # TODO: This implementation could be tidier; use NumPy?
        x = (self._state[0] + self._state[1]) / 2
        y = (self._state[2] + self._state[3]) / 2
        w = self._state[1] - self._state[0]
        assert w == self._state[3] - self._state[2]
        x += self._action[0] * w / 2
        y += self._action[1] * w / 2
        w = round(max(min(w + self._action[2] * w / 2, self.img_size), self.render_size))
        xl, xu = x - w / 2, x + w / 2
        if xl < 0: 
            xl, xu = 0, w
        elif xu > self.img_size: 
            xl, xu = self.img_size - w, self.img_size
        yl, yu = y - w / 2, y + w / 2
        if yl < 0: 
            yl, yu = 0, w
        elif yu > self.img_size: 
            yl, yu = self.img_size - w, self.img_size
        xl, xu, yl, yu = int(round(xl)), int(round(xu)), int(round(yl)), int(round(yu))
        assert xu - xl == yu - yl == int(w)
        self._state = (xl, xu, yl, yu)
        self._obs = self.obs()
        return self._obs, self.reward(), self.done(), {}

    def obs(self): 
        xl, xu, yl, yu = self._state
        return cv2.resize(self.img[yl:yu, xl:xu], (self.render_size, self.render_size))

    def reward(self):       
        return 0.

    def done(self):         
        return False

    def render(self, mode="human", pause=1e-6):
        if mode == "human": 
            assert self.do_render, "Not set up for rendering; initialise with do_render=True"
            self._img_plt.set_data(self._obs)
            self._action_indicator[0].center = self._action[:2]
            w = 2 + self._action[2]
            self._action_indicator[1].xy = self._action[:2] - w / 2
            self._action_indicator[1].set_width(w)
            self._action_indicator[1].set_height(w)
            plt.pause(pause)
        elif mode == "rgb_array": 
            return self._obs 