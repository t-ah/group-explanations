+step : position(Pos) & destination(Dest) & Pos \== Dest <-
  .getPosition(CurrentPos);
  -+position(CurrentPos);
  !reach(Dest).

+!reach(Dest) : position(road(_)) <-
  .drive.

+!reach(Dest) : position(node(Node)) & destination(Node) <-
  .logStep(reached(Node));
  .print("I have reached my destination!");
  -destination(_).

+!reach(Dest) : position(node(Node)) & plannedRoute([NextStop|OtherStops]) <-
  -+plannedRoute(OtherStops);
  !goto(NextStop).

+plannedRoute([]) <- -plannedRoute(_).

+!reach(Dest) : position(node(Node)) <-
  .nextSteps(Node, Dest, Result); //[road(to,length),...] sorted by length
  !chooseNextRoad(Result).

+!reach(Dest) <- .print("I have no idea what to do.").

// never take a road twice
+!chooseNextRoad(Roads)
: position(node(Pos)) & Roads = [road(To, _)|OtherRoads] & usedRoad(Pos, To) <-
  !chooseNextRoad(OtherRoads).

// take road quality into account
+!chooseNextRoad(Roads) // Roads = [road(To, _)|_]
: position(node(Pos)) & Roads = [road(To, _)|_] & minRoadQuality(Q) & edge(Pos, To, _, EdgeQ) & EdgeQ >= Q <-
  !goto(To).

// first element did not satisfy quality criterion
+!chooseNextRoad(Roads)
: position(node(_)) & Roads = [_|Other] & minRoadQuality(_) <-
  !chooseNextRoad(Other).

// no suitable road, take first alternative
+!chooseNextRoad([]) 
: position(node(Pos)) & minRoadQuality(_) & destination(Dest) <-
  .nextSteps(Pos, Dest, [road(To, _)|_]);
  !goto(To).

// simplest plan: always choose the "fastest" road
+!chooseNextRoad(Roads) 
: position(node(_)) & Roads = [road(NextStop, _)|_] <-
  !goto(NextStop).

// handle bridges first
+!goto(To)
: position(node(Pos)) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & waitForBridges <-
  .print("I have to wait for the bridge.").

+!goto(To)
: position(node(Pos)) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & not plannedRoute(_) <-
  .print("I would like to make a detour.");
  .getDetour(To, Detour);
  !useDetour(Detour).

+!goto(NextStop) : position(node(CurrentStop)) <-
  +usedRoad(CurrentStop, NextStop);
  .switchRoad(CurrentStop, NextStop).

+!useDetour([]) <- .print("There is no route to use.").

+!useDetour(Route) : Route = [Next|More] <-
  -+plannedRoute(More);
  !goto(Next).
