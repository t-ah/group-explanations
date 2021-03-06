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
  "agents" : None,
  "trafficImpact" : 0.8,
  "roadLength" : [1,3]
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
  resetWeights()
  for edge in G.edges(position):
    road = G[edge[0]][edge[1]]
    road["w"] = 1000
  for neighbor in G.neighbors(position):
    path_length = nx.shortest_path_length(G, neighbor, destination, "w") + G.get_edge_data(position, neighbor)["length"]
    results.append(pyson.Literal("road", (neighbor, path_length)))
  results.sort(key=lambda x: x.args[1])
  if pyson.unify(term.args[2], tuple(results), intention.scope, intention.stack):
    yield

def resetWeights():
  for (_,_,data) in G.edges(data=True):
    data["w"] = data["length"]

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
    state["roadProgress"] += calculateRoadProgress(trafficData[(node, nextNode)])
    if state["roadProgress"] >= roadData["length"]:
      trafficData[(node, nextNode)] -= 1
      state["node"] = road[1]
      state["path"].append(road[1])
      state["road"] = None
      state["roadProgress"] = 0
    yield
  # check if road is passable
  if G[node][nextNode]["bridge"] and not G[node][nextNode]["bridge"]["open"]:
    yield False
  print("Agent {} using road ({},{})".format(self.name, node, nextNode))
  trafficData[(node, nextNode)] += 1
  roadUsedCounter[(str(node), str(nextNode))] += 1
  state["node"] = None
  state["road"] = (node, nextNode)
  state["roadProgress"] = 0
  yield

def calculateRoadProgress(traffic):
  minProgress = 1 - simConf["trafficImpact"]
  return minProgress + ((1 - minProgress) / (traffic + 1))

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
  destination = agentStates[self.name]["destination"]
  road = G[position][target]
  state = agentStates[self.name]
  resetWeights()
  for edge in G.edges(position):
    # update information for all incident roads
    state["traffic"][edge] = G[edge[0]][edge[1]]["length"] / calculateRoadProgress(trafficData[(edge[0], edge[1])])
    state["traffic"][(edge[1], edge[0])] = G[edge[1]][edge[0]]["length"] / calculateRoadProgress(trafficData[(edge[1], edge[0])])
  for edge, w in state["traffic"].items():
    # use agent's known traffic info
    G[edge[0]][edge[1]]["w"] = w
  path_length = nx.shortest_path_length(G, target, destination, "w") + road["w"]
  if pyson.unify(term.args[1], path_length, intention.scope, intention.stack):
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
      graph.add_edge(edge["fromTo"][0], edge["fromTo"][1], length=edge["length"], quality=edge["quality"], bridge=edge["bridge"], traffic=0)
      if edge.get("bridge"): bridges.append(edge["bridge"])
  else:
    if simConf.get("numberOfNodes"):
      #graph = nx.fast_gnp_random_graph(simConf["numberOfNodes"], 0.02, seed=simConf["randomSeed"], directed=False)
      #graph = nx.barabasi_albert_graph(simConf["numberOfNodes"], 2, simConf["randomSeed"])
      graph = nx.watts_strogatz_graph(simConf["numberOfNodes"], 4, .3, simConf["randomSeed"])
      graph.remove_nodes_from(list(nx.isolates(graph))) # remove isolates
      connected_components = list(nx.connected_components(graph))
      if len(connected_components) > 1:
        print("Connecting connected components.")
        for i in range(len(connected_components) - 1):
          graph.add_edge(connected_components[i].pop(), connected_components[i + 1].pop())
    elif simConf.get("gridDim"):
      graph = nx.grid_graph(dim=simConf["gridDim"])
    for (_,_,data) in graph.edges(data=True):
      lengths = tuple(simConf["roadLength"])
      data["length"] = random.randint(*lengths)
      data["quality"] = random.randint(1,3)
      data["traffic"] = 0
      if random.random() < simConf["pBridge"]:
        data["bridge"] = {
          "open": True,
          "pOpen": 0.1,
          "pClose": 0.3
        }
        bridges.append(data["bridge"])
      else:
        data["bridge"] = None
  graph = nx.DiGraph(graph)
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
        "destination" : random.choice(destinations),
        "traffic" : {}
      }
      state["path"] = [state["node"]]
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
        # beliefs.append(pyson.Literal("edge", (node2, node1, data["length"], data["quality"])))
      for (n1, n2, data) in G.edges(data=True):
        if data["bridge"]:
          beliefs.append(pyson.Literal("bridge", (n1, n2)))
          # beliefs.append(pyson.Literal("bridge", (n2, n1)))
      for belief in beliefs:
        addBelief(agent, belief)

def aggregate(traces):
  roads = defaultdict(lambda: Counter())
  factors_by_path = defaultdict(lambda: defaultdict(lambda: Counter()))
  functorFilter = set(["goto"])
  for ag in env.agents:
    factors = set()
    path = tuple(agentStates[ag]["path"])
    for t in traces[ag]:
      if t.functor == "explain":
        for arg in t.args:
          if arg.functor not in functorFilter:
            factors.add(arg)
      elif t.functor == "action":
        actionArgs = t.args[0].args
        road = roads[actionArgs[0], actionArgs[1]]
        by_path = factors_by_path[actionArgs[0], actionArgs[1]][path]
        for factor in factors:
          road[factor] += 1
          by_path[factor] += 1
        # factors = set() # only take factors for one step into account
  # for road, factors in roads.items():
  #   print("\n\nFactors for {}:".format(road))
  #   for (factor, count) in factors.most_common():
  #     print("{} times {}".format(count, factor))
  for road, paths in factors_by_path.items():
    print("\n\nFactors for {}:".format(road))
    for path, factors in paths.items():
      print("\nPath {}:".format(path))
      for (factor, count) in factors.most_common():
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
  roadUsedCounter = Counter()
  trafficData = defaultdict(int)

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
      pos = state["node"] if state["node"] != None else state["road"]
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

  for n in env.agents:
    print("{} used path {}".format(n, agentStates[n]["path"]))

  # output image and dot file of graph
  for (x,y,data) in G.edges(data=True):
    data["label"] = "len({})".format(data["length"])
  if not os.path.exists("out"): os.makedirs("out")
  cTime = time.time()
  A = nx.nx_agraph.to_agraph(G)
  removeEdges = set()
  for edge in A.edges():
    if edge not in removeEdges: removeEdges.add((edge[1], edge[0]))
  #duplEdges = A.edges()
  #A = A.to_directed()
  #removeEdges = [e for e in A.edges() if e not in duplEdges]
  for edge in removeEdges:
    A.remove_edge(edge)
  A.graph_attr.update(nodesep=1, ranksep=1)
  A.node_attr.update(shape="circle", color="blue", fixedsize="shape")
  A.edge_attr.update(dir="none", labeldistance=2, decorate=True, labelfontsize=8)
  for e in A.edges():
    if e.attr.get("bridge") != "None":
      e.attr["style"] = "dashed,bold"
    e.attr["taillabel"] = roadUsedCounter[e]
    e.attr["headlabel"] = roadUsedCounter[(e[1], e[0])]
  A.layout("dot")
  A.draw(os.path.join("out", "{}.png".format(cTime)))
  nx.nx_agraph.write_dot(G, os.path.join("out", "{}.dot".format(cTime)))