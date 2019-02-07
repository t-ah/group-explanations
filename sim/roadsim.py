#!/usr/bin/env python

import pyson
import pyson.runtime
import pyson.stdlib

import os

import networkx as nx
import matplotlib.pyplot as plt
from random import choice

env = pyson.runtime.Environment()

graph = nx.Graph()
graph.add_edges_from([('A','C'), ('A','tl'), ('A','B'),
                      ('B','tl'), ('B','X'),
                      ('C','X'),
                      ('tl','C'), ('tl','X')])

actions = pyson.Actions(pyson.stdlib.actions)

@actions.add(".perceive", 0)
def perceive(self, term, intention):
  beliefs = [pyson.Literal("name", (self.name, ))]
  beliefs.append(pyson.Literal("destination", (destinations[self], )))
  beliefs.append(pyson.Literal("position", (positions[self], )))
  for node in graph.nodes: 
    beliefs.append(pyson.Literal("node", (node, )))
  for edge in graph.edges:
    beliefs.append(pyson.Literal("edge", (edge[0], edge[1])))
    beliefs.append(pyson.Literal("edge", (edge[1], edge[0])))
  for bel in beliefs:
    self.call(pyson.Trigger.addition, pyson.GoalType.belief, bel, pyson.runtime.Intention())
  yield

@actions.add(".distance", 3)
def distance(self, term, intention):
  n1 = pyson.grounded(term.args[0], intention.scope)
  n2 = pyson.grounded(term.args[1], intention.scope)
  if pyson.unify(term.args[2], nx.shortest_path_length(graph, n1, n2), intention.scope, intention.stack):
    yield

env = pyson.runtime.Environment()

destinations = {}
positions = {}
with open(os.path.join(os.path.dirname(__file__), "car.asl")) as source:
  agents = env.build_agents(source, 2, actions)
  nodes = list(graph.nodes())
  for agent in agents:
    destinations[agent] = choice(nodes)
    positions[agent] = choice(nodes)

if __name__ == "__main__":
  env.run()