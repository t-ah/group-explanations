#!/usr/bin/env python

import pyson
import pyson.runtime
import pyson.stdlib

import os

import networkx as nx
import matplotlib.pyplot as plt
from random import choice

# simulation config
steps = 1
agentsPerStep = 1
initialAgents = 2

env = pyson.runtime.Environment()
actions = pyson.Actions(pyson.stdlib.actions)

@actions.add(".perceive", 0)
def perceive(self, term, intention):
  beliefs = [pyson.Literal("name", (self.name, ))]
  beliefs.append(pyson.Literal("destination", (destinations[self], )))
  beliefs.append(pyson.Literal("position", (positions[self], )))
  for node in graph.nodes():
    beliefs.append(pyson.Literal("node", (node, )))
  for node1, node2, data in graph.edges(data=True):
    beliefs.append(pyson.Literal("edge", (node1, node2, data['traffic'])))
    beliefs.append(pyson.Literal("edge", (node2, node1, data['traffic'])))
  for belief in beliefs:
    addBelief(self, belief)
  yield

@actions.add(".distance", 3)
def distance(self, term, intention):
  n1 = pyson.grounded(term.args[0], intention.scope)
  n2 = pyson.grounded(term.args[1], intention.scope)
  if pyson.unify(term.args[2], nx.shortest_path_length(graph, n1, n2), intention.scope, intention.stack):
    yield

def addBelief(agent, belief):
  agent.call(pyson.Trigger.addition, pyson.GoalType.belief, belief, pyson.runtime.Intention())

def stepSimulation():
  pass

def handlePercepts():
  pass

def createAgents(number):
  with open(os.path.join(os.path.dirname(__file__), "car.asl")) as source:
    agents = env.build_agents(source, number, actions)
    nodes = list(graph.nodes())
    for agent in agents:
      beliefs = [pyson.Literal("name", (agent.name, ))]
      beliefs.append(pyson.Literal("destination", (choice(nodes), )))
      beliefs.append(pyson.Literal("position", (choice(nodes), )))
      for node in graph.nodes():
        beliefs.append(pyson.Literal("node", (node, )))
      for node1, node2, data in graph.edges(data=True):
        beliefs.append(pyson.Literal("edge", (node1, node2)))
        beliefs.append(pyson.Literal("edge", (node2, node1)))
      for belief in beliefs:
        addBelief(agent, belief)

graph = nx.Graph()
graph.add_edges_from([('A','C', {'traffic':'heavy'}), ('A','tl'), ('A','B'),
                      ('B','tl'), ('B','X'),
                      ('C','X'),
                      ('tl','C'), ('tl','X')], traffic='light', weight=1)
# for later: random graphs
# graph = nx.fast_gnp_random_graph(20, 0.15, 17)
# nx.draw(graph)
# plt.show()

createAgents(initialAgents)

if __name__ == "__main__":
  for step in range(steps):
    print("SIMULATION AT STEP %s") % step
    stepSimulation()
    createAgents(agentsPerStep)
    handlePercepts()
    env.run()
  # gather new positions from agents
  # build a simple schedule