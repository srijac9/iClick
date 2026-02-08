import numpy as np
from collections import deque

class CursorSmoother:
    def __init__(self, buffer_size=5, min_movement=3, max_speed=150):
        """
        buffer_size: Number of positions to average
        min_movement: Ignore movements smaller than this many pixels
        max_speed: Maximum pixels cursor can move per frame
        """
        self.buffer_x = deque(maxlen=buffer_size)
        self.buffer_y = deque(maxlen=buffer_size)
        self.last_x = None
        self.last_y = None
        self.min_movement = min_movement
        self.max_speed = max_speed
        
    def smooth(self, x, y):
        """Returns smoothed (x, y) coordinates"""
        # Add to buffers
        self.buffer_x.append(x)
        self.buffer_y.append(y)
        
        # Calculate weighted average (recent positions weighted more)
        if len(self.buffer_x) > 1:
            weights = np.exp(np.linspace(0, 1, len(self.buffer_x)))
            smooth_x = np.average(list(self.buffer_x), weights=weights)
            smooth_y = np.average(list(self.buffer_y), weights=weights)
        else:
            smooth_x, smooth_y = x, y
        
        # Initialize on first call
        if self.last_x is None:
            self.last_x, self.last_y = smooth_x, smooth_y
            return int(smooth_x), int(smooth_y)
        
        # Calculate movement
        dx = smooth_x - self.last_x
        dy = smooth_y - self.last_y
        distance = np.sqrt(dx**2 + dy**2)
        
        # Ignore tiny movements (deadzone)
        if distance < self.min_movement:
            return int(self.last_x), int(self.last_y)
        
        # Cap maximum speed
        if distance > self.max_speed:
            scale = self.max_speed / distance
            dx *= scale
            dy *= scale
        
        # Update position
        self.last_x += dx
        self.last_y += dy
        
        return int(self.last_x), int(self.last_y)