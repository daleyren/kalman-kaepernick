# Kalshi-style DQN agent that only allows one bet (yes/no) per episode
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque
import random

class QNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=64):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, action_dim)

    def forward(self, x):
        if isinstance(x, np.ndarray):
            x = torch.FloatTensor(x)
        x = F.relu(self.fc1(x))
        return self.fc2(x)

class ReplayBuffer:
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)

    def add(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)

class KalshiPolicy:
    def __init__(self, state_dim, action_dim, lr=0.001, gamma=0.99, epsilon=1.0):
        self.state_dim = state_dim
        self.action_dim = action_dim  # 0 = hold, 1 = buy YES, 2 = buy NO
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.99
        self.batch_size = 64

        self.q_network = QNetwork(state_dim, action_dim)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=lr)
        self.replay_buffer = ReplayBuffer()
        self.bet_placed = False

    def sample_action(self, state):
        if self.bet_placed:
            return 0  # Hold if bet already placed

        if np.random.rand() <= self.epsilon:
            return np.random.choice(self.action_dim)

        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        self.q_network.eval()
        with torch.no_grad():
            q_values = self.q_network(state_tensor)
        return torch.argmax(q_values, dim=1).item()

    def __call__(self, state, action, reward, next_state, done):
        self.replay_buffer.add(state, action, reward, next_state, done)
        if action in [1, 2]:
            self.bet_placed = True

        if len(self.replay_buffer) < self.batch_size:
            return

        batch = self.replay_buffer.sample(self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions).unsqueeze(1)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones)

        current_q_values = self.q_network(states).gather(1, actions)
        with torch.no_grad():
            max_next_q = self.q_network(next_states).max(1)[0]
            target_q_values = rewards + self.gamma * max_next_q * (1 - dones)
            target_q_values = target_q_values.unsqueeze(1)

        loss = F.mse_loss(current_q_values, target_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if done:
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
            self.bet_placed = False  # reset for next episode
