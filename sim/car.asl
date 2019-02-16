satisfiesQuality(From, To) :- minRoadQuality(MinQ) & edge(From, To, _, RoadQ) & RoadQ >= MinQ.

+destination(Dest) <- .print("I want to go to", Dest).
// is added before step; for cleaning up beliefs etc.
+beforeStep <- -position(_).
// step percept is added at the beginning of each simulation step
+step : destination(Dest) <- .print("step"); !reach(Dest).

+!reach(Dest) : position([N1,N2]) & edge(N1, N2, _, _) <-
  .takeRoad(N1, N2).
+!reach(Dest) : position(Node) & destination(Node) <-
  .logStep(explain(reach(Dest), atDestination(Node)));
  -destination(_).
+!reach(Dest) : position(Node) & plannedRoute([NextStop|OtherStops]) <-
  .logStep(explain(reach(Dest), plannedRoute([NextStop|OtherStops]), notAtDestination(Node)));
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
  .nextSteps(Pos, Dest, Roads);
  !filterByQuality(Roads, []).
// filtering done - some roads remain
+!filterUsed([], Unused) <-
  !filterByQuality(Unused, []).
// road has already been used - discard
+!filterUsed([road(To, _)|OtherRoads], Unused) : position(Pos) & usedRoad(Pos, To) <-
  !filterUsed(OtherRoads, Unused).
// finding an unused road
+!filterUsed([UnusedRoad|OtherRoads], Unused) <-
  .concat(Unused, [UnusedRoad], NewUnused);
  !filterUsed(OtherRoads, NewUnused).

// no road passed quality criterion, continue with all roads
+!filterByQuality([],[]) : position(Pos) & destination(Dest) <-
  .nextSteps(Pos, Dest, Roads);
  !checkTraffic(Roads).
// filtering done - some roads remain
+!filterByQuality([], GoodRoads) <-
  !checkTraffic(GoodRoads).
// finding an acceptable road
+!filterByQuality([road(To, L)|OtherRoads], GoodRoads) : position(Pos) & satisfiesQuality(Pos, To) <-
  .concat(GoodRoads, [road(To, L)], NewGoodRoads);
  !filterByQuality(OtherRoads, NewGoodRoads).
// the road can only be unacceptable
+!filterByQuality([_|OtherRoads], GoodRoads) <-
  !filterByQuality(OtherRoads, GoodRoads).

// only one road (left) to take
+!checkTraffic(Roads) : .length(Roads, 1) <-
  .nth(0, Roads, road(To,_));
  !goto(To).
// filter roads by traffic (at least two roads)
+!checkTraffic(Roads) <-
  Roads = [road(R1, L1)|[road(R2, L2)|OtherRoads]];
  .getTraffic(R1, T1);
  .getTraffic(R2, T2);
  if (L1 + T1 > L2 + T2) { .concat([road(R2, L2)], OtherRoads, BestRoads); }
  else                   { .concat([road(R1, L1)], OtherRoads, BestRoads); }
  !checkTraffic(BestRoads).

// handle bridges first
+!goto(To) : position(Pos) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & waitForBridges <-
  .print("I have to wait for the bridge.").
+!goto(To) : position(Pos) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & not plannedRoute(_) <-
  .getDetour(To, Detour);
  !useDetour(Detour).
+!goto(NextStop) : position(CurrentStop) <-
  +usedRoad(CurrentStop, NextStop);
  .takeRoad(CurrentStop, NextStop).

+!useDetour([]) <- .print("There is no route to use.").
+!useDetour(Route) : Route = [Next|More] <-
  -+plannedRoute(More);
  !goto(Next).