satisfiesQuality(From, To) :- minRoadQuality(MinQ) & edge(From, To, _, RoadQ) & RoadQ >= MinQ.

+destination(Dest) <- .print("I want to go to", Dest).
// is added before step; for cleaning up beliefs etc.
+beforeStep <- -position(_).
// step percept is added at the beginning of each simulation step
+step : destination(Dest) <- !reach(Dest).

+!reach(Dest) : position([N1,N2]) & edge(N1, N2, _, _) <-
  .takeRoad(N1, N2).
+!reach(Dest) : position(Node) & destination(Node) <-
  .logStep(explain(reach(Dest), atDestination(Node)));
  -destination(_).
+!reach(Dest) : position(Node) & plannedRoute([NextStop|OtherStops]) <-
  .logStep(explain(reach(Dest), notAtDestination(Node), plannedRoute([NextStop|OtherStops])));
  -+plannedRoute(OtherStops);
  !goto(NextStop).
+!reach(Dest) : position(Node) <-
  .logStep(explain(reach(Dest), notAtDestination, noPlannedRoute));
  .nextSteps(Node, Dest, Roads); //[road(to,length),...] sorted by length
  !filterUsed(Roads, []).
+!reach(Dest) <- .print("I have no idea what to do.").

+plannedRoute([]) <- -plannedRoute(_).

// no road unused, continue with all roads
+!filterUsed([],[]) : position(Pos) & destination(Dest) <-
  .logStep(explain(filterUsed([],[])));
  .nextSteps(Pos, Dest, Roads);
  !filterByQuality(Roads, Roads, []).
// filtering done - some roads remain
+!filterUsed([], Unused) <-
  .logStep(explain(filterUsed([], Unused)));
  !filterByQuality(Unused, Unused, []).
// road has already been used - discard
+!filterUsed([road(To, L)|OtherRoads], Unused) : position(Pos) & usedRoad(Pos, To) <-
  .logStep(explain(filterUsed([road(To, L)|OtherRoads], Unused), usedRoad(Pos, To)));
  !filterUsed(OtherRoads, Unused).
// finding an unused road
+!filterUsed([UnusedRoad|OtherRoads], Unused) <-
  position(Pos); UnusedRoad = road(To, _); // only used for explanation
  .logStep(explain(filterUsed([UnusedRoad|OtherRoads], Unused), notUsedRoad(Pos, To)));
  .concat(Unused, [UnusedRoad], NewUnused);
  !filterUsed(OtherRoads, NewUnused).

// no road passed quality criterion, continue with all previous roads
+!filterByQuality(Roads, [],[]) : position(Pos) & destination(Dest) <-
  .logStep(explain(filterByQuality([],[])));
  !checkTraffic(Roads).
// filtering done - some roads remain
+!filterByQuality(_, [], GoodRoads) <-
  .logStep(explain(filterByQuality([], GoodRoads)));
  !checkTraffic(GoodRoads).
// finding an acceptable road
+!filterByQuality(PrevRoads, [road(To, L)|OtherRoads], GoodRoads) : position(Pos) & satisfiesQuality(Pos, To) <-
  .logStep(explain(filterByQuality([road(To, L)|OtherRoads], GoodRoads), satisfiesQuality(Pos, To)));
  .concat(GoodRoads, [road(To, L)], NewGoodRoads);
  !filterByQuality(PrevRoads, OtherRoads, NewGoodRoads).
// the road can only be unacceptable
+!filterByQuality(PrevRoads, [BadRoad|OtherRoads], GoodRoads) <-
  position(Pos); BadRoad = road(To, _);
  .logStep(explain(filterByQuality([BadRoad|OtherRoads], GoodRoads), notSatisfiesQuality(Pos, To)));
  !filterByQuality(PrevRoads, OtherRoads, GoodRoads).

// only one road (left) to take
+!checkTraffic(Roads) : .length(Roads, 1) <-
  .logStep(explain(checkTraffic(Roads), oneRoad));
  .nth(0, Roads, road(To,_));
  !goto(To).
// filter roads by traffic (at least two roads)
+!checkTraffic(Roads) <-
  .logStep(explain(checkTraffic(Roads), moreThanOneRoad));
  Roads = [road(R1, L1)|[road(R2, L2)|OtherRoads]];
  .getTraffic(R1, T1);
  .getTraffic(R2, T2);
  if (L1 + T1 > L2 + T2) { .concat([road(R2, L2)], OtherRoads, BestRoads); .logStep(explain(checkTraffic(Roads), preferTraffic(R2))); }
  else                   { .concat([road(R1, L1)], OtherRoads, BestRoads); .logStep(explain(checkTraffic(Roads), preferTraffic(R1))); }
  !checkTraffic(BestRoads).

// handle bridges first
+!goto(To) : position(Pos) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & waitForBridges <-
  .logStep(explain(goto(To), closedBridge, waitForBridges));
  .print("I have to wait for the bridge.").
+!goto(To) : position(Pos) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) <-
  .logStep(explain(goto(To), closedBridge, notWaitForBridges));
  .getDetour(To, Detour);
  !useDetour(Detour).
+!goto(To) : position(Pos) & bridge(Pos, To) <-
  .logStep(explain(goto(To), bridgeOpen(Pos, To)));
  +usedRoad(Pos, To); .takeRoad(Pos, To).
+!goto(To) : position(Pos) <-
  .logStep(explain(goto(To), noBridge));
  +usedRoad(Pos, To); .takeRoad(Pos, To).

+!useDetour([]) <- .print("There is no route to use.").
+!useDetour([Next|More]) <-
  .logStep(explain(useDetour([Next|More])));
  -+plannedRoute(More);
  !goto(Next).