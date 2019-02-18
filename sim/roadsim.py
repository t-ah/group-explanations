#!/usr/bin/env python

import pyson
import pyson.runtime
import pyson.stdlib

import os, sys
import time
import networkx as nx
import pygraphviz as pgv
import random
import json
from collections import Counter, defaultdict

# simulation config
simConf = {
  "steps" : 100,
  "agentsPerStep" : 0,
  "initialAgents" : 5,
  "numberOfNodes" : None, # for gnp graphs
  "gridDim" : [5,5], # for grid-like graphs
  "pBridge" : 0.15,
  "randomSeed" : 17,
  "graph" : None,
  "agents" : None
}

# setup pyson
env = pyson.runtime.Environment()
actions = pyson.Actions(pyson.stdlib.actions)

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

@actions.add(".takeRoad", 2)
def takeRoad(self, term, intention):
  node = pyson.grounded(term.args[0], intention.scope)
  nextNode = pyson.grounded(term.args[1], intention.scope)
  if not G.has_edge(node, nextNode):
    yield False
  state = agentStates[self.name]
  if state["road"] in [(node, nextNode), (nextNode, node)]:
    # stay on road
    road = state["road"]
    roadData = G[node][nextNode]
    state["roadProgress"] += calculateRoadProgress(roadData["traffic"])
    if state["roadProgress"] >= roadData["length"]:
      roadData["traffic"] -= 1
      state["node"] = road[1]
      state["road"] = None
      state["roadProgress"] = 0
    yield
  # check if road is passable
  if G[node][nextNode]["bridge"] and not G[node][nextNode]["bridge"]["open"]:
    yield False
  print("Agent {} using road ({},{})".format(self.name, node, nextNode))
  G[node][nextNode]["traffic"] += 1
  G[node][nextNode]["used"] += 1
  state["node"] = None
  state["road"] = (node, nextNode)
  state["roadProgress"] = 0
  yield

def calculateRoadProgress(traffic):
  return 0.1 + (0.9 / (traffic + 1))

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

@actions.add(".getTraffic", 2)
def getTraffic(self, term, intention):
  target = pyson.grounded(term.args[0], intention.scope)
  position = agentStates[self.name]["node"]
  road = G[position][target]
  stepsNeeded = road["length"] / calculateRoadProgress(road["traffic"])
  additionalSteps = stepsNeeded - road["length"]
  if pyson.unify(term.args[1], additionalSteps, intention.scope, intention.stack):
    yield

@actions.add(".logStep", 1)
def logStep(self, term, intention):
  content = pyson.grounded(term.args[0], intention.scope)
  traces[self.name].append(content)
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
  bridges = []
  if simConf.get("graph"):
    graph = nx.Graph()
    for edge in simConf["graph"]:
      graph.add_edge(edge["fromTo"][0], edge["fromTo"][1], length=edge["length"], quality=edge["quality"], bridge=edge["bridge"], traffic=0, used=0)
      if edge.get("bridge"): bridges.append(edge["bridge"])
  else:
    if simConf.get("numberOfNodes"):
      graph = nx.fast_gnp_random_graph(simConf["numberOfNodes"], 0.2, seed=simConf["randomSeed"], directed=False)
    elif simConf.get("gridDim"):
      graph = nx.grid_graph(dim=simConf["gridDim"])
    for (_,_,data) in graph.edges(data=True):
      data["length"] = random.randint(1,3)
      data["quality"] = random.randint(1,3)
      data["traffic"] = 0
      data["used"] = 0
      if random.random() < simConf["pBridge"]:
        data["bridge"] = {
          "open": True,
          "pOpen": 0.1,
          "pClose": 0.1
        }
        bridges.append(data["bridge"])
      else:
        data["bridge"] = None
  return (bridges, graph)

def createAgents(G, number):
  with open(os.path.join(os.path.dirname(__file__), "car.asl")) as source:
    agents = env.build_agents(source, number, actions)
    nodes = list(G.nodes())
    positions = simConf["agents"]["positions"] if simConf.get("agents") else nodes
    destinations = simConf["agents"]["destinations"] if simConf.get("agents") else nodes
    for agent in agents:
      beliefs = [pyson.Literal("name", (agent.name, ))]
      state = {
        "node" : random.choice(positions),
        "road" : None,
        "roadProgress" : 0,
        "destination" : random.choice(destinations)
      }
      agentStates[agent.name] = state
      # generate traits/preferences:
      beliefs.append(pyson.Literal("minRoadQuality", (random.randint(0, 3), )))
      if random.random() < 0.5:
        beliefs.append(pyson.Literal("waitForBridges"))
      # add general beliefs
      beliefs.append(pyson.Literal("destination", (state["destination"], )))
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

def aggregate(traces):
  roads = defaultdict(lambda: Counter())
  functorFilter = set(["goto"])
  for ag in env.agents:
    factors = set()
    for t in traces[ag]:
      if t.functor == "explain":
        for arg in t.args:
          if arg.functor not in functorFilter:
            factors.add(arg)
      elif t.functor == "action":
        actionArgs = t.args[0]
        road = roads[actionArgs.args[0], actionArgs.args[1]]
        for factor in factors:
          road[factor] += 1
        # factors = set() # only take factors for one step into account
  for road, factors in roads.items():
    print("\n\nFactors for {}:".format(road))
    for (factor, count) in factors.most_common(15):
      print("{} times {}".format(count, factor))

if __name__ == "__main__":
  # setup simulation
  if len(sys.argv) > 1:
    configFile = sys.argv[1]
    with open(configFile) as f:
      jsonConf = json.load(f)
      for k in simConf:
        if k in jsonConf:
          simConf[k] = jsonConf[k]

  random.seed(simConf["randomSeed"])
  agentStates = {}
  bridges, G = setupGraph()
  createAgents(G, simConf["initialAgents"])
  traces = dict([(key, []) for key in env.agents])

  # run simulation
  for step in range(simConf["steps"]):
    unfinished = list(filter(lambda x: x["node"] != x["destination"], agentStates.values()))
    if len(unfinished) == 0:
      print("SIMULATION FINISHED")
      break
    print("SIMULATION AT STEP {}".format(step))
    stepSimulation()
    createAgents(G, simConf["agentsPerStep"])
    handlePercepts()
    for agent in sorted(env.agents.values(), key=lambda ag: ag.name):
      addBelief(agent, pyson.Literal("beforeStep"))
      env.run_agent(agent)
      state = agentStates[agent.name]
      pos = state["node"] if state["node"] else state["road"]
      addBelief(agent, pyson.Literal("position", (pos,)))
      addBelief(agent, pyson.Literal("step"))
      env.run_agent(agent)

  # simulation results
  # print("\nTrace of agent 'car':")
  # for t in traces["car"]:
  #   print(t)
  # print(traces)

  print("\nTraces of other cars ... ")
  for n in env.agents:
    print("\n\nTrace of agent {}".format(n))
    for t in traces[n]:
      print(t)

  aggregate(traces)

  # output image and dot file of graph
  for (x,y,data) in G.edges(data=True):
    data["label"] = "len({}),q({}),u({})".format(data["length"], data["quality"], data["used"])
  if not os.path.exists("out"): os.makedirs("out")
  cTime = time.time()
  A = nx.nx_agraph.to_agraph(G)
  A.node_attr.update(shape="box", color="blue")
  for e in A.edges():
    if e.attr.get("bridge") != "None":
      e.attr["style"] = "dashed,bold"
  A.layout("dot")

  A.draw(os.path.join("out", "{}.png".format(cTime)))
  nx.nx_agraph.write_dot(G, os.path.join("out", "{}.dot".format(cTime)))