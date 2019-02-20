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
  .logStep(explain(reach(Dest), notAtDestination(Node)));
  .logStep(explain(plannedRoute([NextStop|OtherStops])));
  -+plannedRoute(OtherStops);
  !goto(NextStop).
+!reach(Dest) : position(Node) <-
  .logStep(explain(reach(Dest))); 
  .logStep(explain(notAtDestination, noPlannedRoute));
  .nextSteps(Node, Dest, Roads); //[road(to,length),...] sorted by length
  !filterUsed(Roads, []).
+!reach(Dest) <- .print("I have no idea what to do.").

+plannedRoute([]) <- -plannedRoute(_).

// no road unused, continue with all roads
+!filterUsed([],[]) : position(Pos) & destination(Dest) <-
  .nextSteps(Pos, Dest, Roads);
  //!filterByQuality(Roads, Roads, []).
  !checkTraffic(Roads).
// filtering done - some roads remain
+!filterUsed([], Unused) <-
  //!filterByQuality(Unused, Unused, []).
  !checkTraffic(Unused).
// road has already been used - discard
+!filterUsed([road(To, L)|OtherRoads], Unused) : position(Pos) & usedRoad(Pos, To) <-
  .logStep(explain(usedRoad(Pos, To)));
  !filterUsed(OtherRoads, Unused).
// finding an unused road
+!filterUsed([UnusedRoad|OtherRoads], Unused) <-
  position(Pos); UnusedRoad = road(To, _); // only used for explanation
  .concat(Unused, [UnusedRoad], NewUnused);
  !filterUsed(OtherRoads, NewUnused).

// only one road (left) to take
+!checkTraffic([road(To, _)]) <-
  !goto(To).
// filter roads by traffic (at least two roads)
+!checkTraffic(Roads) : position(Pos) <-
  Roads = [road(R1, L1)|[road(R2, L2)|OtherRoads]];
  .getTraffic(R1, T1);
  .getTraffic(R2, T2);
  if (T1 > T2) {
    .concat([road(R2, L2)], OtherRoads, BestRoads);
  }
  else {
    .concat([road(R1, L1)], OtherRoads, BestRoads);
  }
  if ((L1>L2) & (T2>T1)) {
    .logStep(explain(would_prefer_due_to_traffic([Pos,R1],[Pos,R2])));
  }
  if ((L2>L1) & (T1>T2)) {
    .logStep(explain(would_prefer_due_to_traffic([Pos,R2],[Pos,R1])));
  }
  if ((L1>L2) & (T2<=T1)) {
    .logStep(explain(would_prefer_due_to_route_length([Pos,R2],[Pos,R1])));
  }
  if ((L2>L1) & (T1<=T2)) {
    .logStep(explain(would_prefer_due_to_route_length([Pos,R1],[Pos,R2])));
  }
  !checkTraffic(BestRoads).

// handle bridges first
+!goto(To) : position(Pos) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & waitForBridges <-
  .logStep(explain(goto(To), waitForClosedBridge(Pos, To))).
+!goto(To) : position(Pos) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & not plannedRoute(_) <-
  .logStep(explain(goto(To), notWaitForClosedBridge(Pos, To)));
  !useDetour(To).
+!goto(To) : position(Pos) & bridge(Pos, To) <-
  .logStep(explain(goto(To), bridgeOpen(Pos, To)));
  .logStep(action(takeRoad(Pos,To))); .logStep(explain(tookRoad(Pos, To)));
  +usedRoad(Pos, To); .takeRoad(Pos, To).
+!goto(To) : position(Pos) <-
  .logStep(explain(goto(To), noBridge(Pos, To)));
  .logStep(action(takeRoad(Pos,To))); .logStep(explain(tookRoad(Pos, To)));
  +usedRoad(Pos, To); .takeRoad(Pos, To).

+!useDetour([]) <- .print("There is no route to use.").
+!useDetour(To) : position(Pos) <-
  .getDetour(To, Detour);
  if (.member(To, Detour)) {
    //.print("There is no detour, I have to use the bridge.");
    .logStep(explain(cannotUseDetour(Pos, To)));
  }
  else {
    .logStep(explain(useDetourAround(Pos, To)));
    Detour = [Next|More];
    -+plannedRoute(More);
    !goto(Next);
  }.