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
numberOfNodes = 30
pBridge = 0.15
randomSeed = 17


random.seed(randomSeed)

env = pyson.runtime.Environment()
actions = pyson.Actions(pyson.stdlib.actions)
agentStates = {}

@actions.add(".getPosition", 1)
def getPosition(self, term, intention):
  state = agentStates[self.name]
  belief = pyson.Literal("road", (state["road"],)) if state["road"] else pyson.Literal("node", (state["node"],))
  if pyson.unify(term.args[0], belief, intention.scope, intention.stack):
    yield

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
  print("Agent {} using road ({},{})".format(self.name, node, nextNode))
  state = agentStates[self.name]
  state["node"] = None
  state["road"] = (node, nextNode)
  state["roadProgress"] = 0
  yield

@actions.add(".bridgeStatus", 3)
def bridgeStatus(self, term, intention):
  node1 = pyson.grounded(term.args[0], intention.scope)
  node2 = pyson.grounded(term.args[1], intention.scope)
  result = G.get_edge_data(node1, node2)["bridge"]["open"]
  if pyson.unify(term.args[2], pyson.Literal("open", (result,)), intention.scope, intention.stack):
    yield

@actions.add(".getDetour", 2)
def getDetour(self, term, intention):
  target = pyson.grounded(term.args[0], intention.scope)
  position = agentStates[self.name]["node"]
  edgeData = G.get_edge_data(position, target)
  length = edgeData["length"]
  edgeData["length"] = 10000
  path = nx.shortest_path(G, position, target, "length")[1:]
  edgeData["length"] = length
  if pyson.unify(term.args[1], tuple(path), intention.scope, intention.stack):
    yield

@actions.add(".logStep", 1)
def logStep(self, term, intention):
  content = pyson.grounded(term.args[0], intention.scope)
  traces[self.name].append(str(content))
  yield

def addBelief(ag, belief):
  ag.call(pyson.Trigger.addition, pyson.GoalType.belief, belief, pyson.runtime.Intention())

def stepSimulation():
  for bridge in bridges:
    if bridge["open"]:
      if random.random() < bridge["pClose"]:
        bridge["open"] = False
    else:
      if random.random() < bridge["pOpen"]:
        bridge["open"] = True

def handlePercepts():
  pass

def setupGraph():
  #graph = nx.fast_gnp_random_graph(numberOfNodes, 0.2, seed=randomSeed, directed=False)
  graph = nx.grid_graph(dim=[5,5])
  bridges = []
  for (_,_,data) in graph.edges(data=True):
    data["length"] = random.randint(1,3)
    data["quality"] = random.randint(1,3)
    if random.random() < pBridge:
      data["bridge"] = {
        "open": True,
        "pOpen": 0.1,
        "pClose": 0.1
      }
      bridges.append(data["bridge"])
    else:
      data["bridge"] = False
  return (bridges, graph)

def createAgents(G, number):
  with open(os.path.join(os.path.dirname(__file__), "car.asl")) as source:
    agents = env.build_agents(source, number, actions)
    nodes = list(G.nodes())
    for agent in agents:
      beliefs = [pyson.Literal("name", (agent.name, ))]
      state = {
        "node" : random.choice(nodes),
        "road" : None,
        "roadProgress" : 0,
        "destination" : random.choice(nodes)
      }
      agentStates[agent.name] = state
      # generate traits/preferences:
      if random.random() < 0.8:
        beliefs.append(pyson.Literal("minRoadQuality", (random.randint(1,3), )))
      if random.random() < 0.5:
        beliefs.append(pyson.Literal("waitForBridges"))
      # add general beliefs
      beliefs.append(pyson.Literal("destination", (state["destination"], )))
      beliefs.append(pyson.Literal("position", (state["node"], )))
      for node in G.nodes():
        beliefs.append(pyson.Literal("node", (node, )))
      for node1, node2, data in G.edges(data=True):
        beliefs.append(pyson.Literal("edge", (node1, node2, data["length"], data["quality"])))
        beliefs.append(pyson.Literal("edge", (node2, node1, data["length"], data["quality"])))
      for (n1, n2, data) in G.edges(data=True):
        if data["bridge"]:
          beliefs.append(pyson.Literal("bridge", (n1, n2)))
          beliefs.append(pyson.Literal("bridge", (n2, n1)))
      for belief in beliefs:
        addBelief(agent, belief)

bridges, G = setupGraph()
createAgents(G, initialAgents)
traces = dict([(key, []) for key in env.agents])

if __name__ == "__main__":
  for step in range(steps):
    print("SIMULATION AT STEP {}".format(step))
    stepSimulation()
    createAgents(G, agentsPerStep)
    handlePercepts()
    for agent in env.agents.values():
      addBelief(agent, pyson.Literal("step"))
    env.run()

  print("\nTrace of agent 'car4':")
  for t in traces["car4"]: 
    print(t)
  # print(traces)
  pos = nx.spring_layout(G, iterations=500)
  nx.draw(G, pos, node_size=800)
  edgeLabels = {}
  for (x,y,data) in G.edges(data=True):
    if data["bridge"]: edgeLabels[(x,y)] = "bridge"
  nx.draw_networkx_edge_labels(G, pos, edge_labels=edgeLabels)
  nodeLabels = {}
  for node in G:
    nodeLabels[node] = node
  nx.draw_networkx_labels(G, pos, nodeLabels)
  plt.show()