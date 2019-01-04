import random
import torch
import torch.nn as nn
import torch.nn.functional as F
from agents.base_agent import Agent
from dex import *

class ReplayMemory:
    def __init__(self, capacity):
        self.capaciy = capacity
        self.memory = []
        self.position = 0

    def push(self, replay):
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = replay
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)


class Network(nn.Module):
    def __init__(self, poke_len, move_len, item_len, ability_len):
        super().__init__()
        embed_dim = 10
        self.poke_embed = nn.Embedding(poke_len, embed_dim)
        self.ability_embed = nn.Embedding(ability_len, embed_dim)
        self.move_embed = nn.Embedding(move_len, embed_dim)
        self.item_embed = nn.Embedding(item_len, embed_dim)
        #num poke features, adjusted for embeddings and multiplications
        p = 45 + embed_dim * 3 - 6
        h1 = 100
        h2 = 60
        self.poke_fc1 = nn.Linear(p, h1)
        self.poke_fc2 = nn.Linear(h1, h2)

    def forward(self, inputs):
        #inputs has the structure specified in base_agent.to_features
        pokes = inputs[0:552].reshape([12, 45]).t()
        self.poke_forward(pokes)

    def poke_forward(self, inputs):
        #Deal with missing data by multiplying features with a "known" feature
        x = torch.cat((
            self.poke_embed(inputs[0]),
            torch.mul(self.ability_embed(inputs[1]), inputs[2]),
            inputs[3:37],
            torch.mul(self.item_embed(inputs[37]), inputs[38]),
            torch.mul(inputs[39:44], inputs[44]))
        , dim=-1)
        x = F.relu(self.poke_fc1(x))
        x = F.relu(self.poke_fc2(x))
        x = torch.mul(x, inputs[45])
        return x

class DQNAgent(Agent):
    pass
