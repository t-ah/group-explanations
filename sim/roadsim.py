#!/usr/bin/env python

import pyson
import pyson.runtime
import pyson.stdlib

import os
import networkx as nx
import matplotlib.pyplot as plt
import random

# simulation config
steps = 100
agentsPerStep = 0
initialAgents = 5

env = pyson.runtime.Environment()
actions = pyson.Actions(pyson.stdlib.actions)
agentStates = {}

@actions.add(".distance", 3)
def distance(self, term, intention):
  n1 = pyson.grounded(term.args[0], intention.scope)
  n2 = pyson.grounded(term.args[1], intention.scope)
  if pyson.unify(term.args[2], nx.shortest_path_length(G, n1, n2), intention.scope, intention.stack):
    yield

@actions.add(".nextSteps", 3)
def nextSteps(self, term, intention):
  position = pyson.grounded(term.args[0], intention.scope)
  destination = pyson.grounded(term.args[1], intention.scope)
  results = []
  for neighbor in G.neighbors(position):
    path_length = nx.shortest_path_length(G, neighbor, destination, "length") + G.get_edge_data(position, neighbor)["length"]
    results.append(pyson.Literal("road", (neighbor, path_length)))
  results.sort(key=lambda x: x.args[1])
  if pyson.unify(term.args[2], tuple(results), intention.scope, intention.stack):
    yield

@actions.add(".drive", 0)
def drive(self, term, intention):
  state = agentStates[self.name]
  state["roadProgress"] += 1
  if state["roadProgress"] == G.get_edge_data(*state["road"])["length"]:
    state["node"] = state["road"][1]
    state["road"] = None
    state["roadProgress"] = 0
  yield

@actions.add(".switchRoad", 2)
def switchRoad(self, term, intention):
  node = pyson.grounded(term.args[0], intention.scope)
  nextNode = pyson.grounded(term.args[1], intention.scope)
  print("Agent %s switching from %s to %s") % (self.name, node, nextNode)
  state = agentStates[self.name]
  state["node"] = None
  state["road"] = (node, nextNode)
  state["roadProgress"] = 0
  yield

def addBelief(ag, belief):
  ag.call(pyson.Trigger.addition, pyson.GoalType.belief, belief, pyson.runtime.Intention())

def stepSimulation():
  # handle bridges
  pass

def handlePercepts():
  for agent in env.agents.values():
    state = agentStates[agent.name]
    if state["road"]:
      addBelief(agent, pyson.Literal("onRoad"))
    else:
      addBelief(agent, pyson.Literal("atIntersection", (state["node"],)))

def createAgents(number):
  with open(os.path.join(os.path.dirname(__file__), "car.asl")) as source:
    agents = env.build_agents(source, number, actions)
    nodes = list(G.nodes())
    # TODO give each agent random characteristics/preferences
    for agent in agents:
      beliefs = [pyson.Literal("name", (agent.name, ))]
      state = {
        "node" : random.choice(nodes),
        "road" : None,
        "roadProgress" : 0,
        "destination" : random.choice(nodes)
      }
      agentStates[agent.name] = state
      beliefs.append(pyson.Literal("destination", (state["destination"], )))
      beliefs.append(pyson.Literal("position", (state["node"], )))
      beliefs.append(pyson.Literal("minRoadQuality", (random.randint(1,3), )))
      for node in G.nodes():
        beliefs.append(pyson.Literal("node", (node, )))
      for node1, node2, data in G.edges(data=True):
        beliefs.append(pyson.Literal("edge", (node1, node2, data["length"], data["quality"])))
        beliefs.append(pyson.Literal("edge", (node2, node1, data["length"], data["quality"])))
      for belief in beliefs:
        addBelief(agent, belief)

G = nx.fast_gnp_random_graph(30, 0.2, seed=17, directed=False)
for (_,_,data) in G.edges(data=True):
  data["length"] = random.randint(1,3)
  data["quality"] = random.randint(1,3)
# TODO assign bridges

createAgents(initialAgents)

if __name__ == "__main__":
  for step in range(steps):
    print("SIMULATION AT STEP %s") % step
    stepSimulation()
    createAgents(agentsPerStep)
    handlePercepts()
    for agent in env.agents.values():
      addBelief(agent, pyson.Literal("step"))
    env.run()