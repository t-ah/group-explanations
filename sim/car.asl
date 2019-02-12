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
  .logStep(reach(NextStop, "partOfPlannedRoute"));
  -+plannedRoute(OtherStops);
  !goto(NextStop).

+plannedRoute([]) <- -plannedRoute(_).

+!reach(Dest) : position(node(Node)) <-
  .logStep(reach("planNextStop", "noRoutePlanned"));
  .nextSteps(Node, Dest, Result); //[road(to,length),...] sorted by length
  !chooseNextRoad(Result).

+!reach(Dest) <- .print("I have no idea what to do.").

// never take a road twice
+!chooseNextRoad(Roads)
: position(node(Pos)) & Roads = [road(To, _)|OtherRoads] & usedRoad(Pos, To) <-
  .logStep(choose(exclude(Pos,To,"used")));
  !chooseNextRoad(OtherRoads).

// take road quality into account
+!chooseNextRoad(Roads) // Roads = [road(To, _)|_]
: position(node(Pos)) & Roads = [road(To, _)|_] & minRoadQuality(Q) & edge(Pos, To, _, EdgeQ) & EdgeQ >= Q <-
  .logStep(choose(Pos,To,"unused","acceptQuality"));
  !goto(To).

// first element did not satisfy quality criterion
+!chooseNextRoad(Roads)
: position(node(Pos)) & Roads = [First|Other] & minRoadQuality(_) <-
  .logStep(choose(Pos,First,"unused",discard("lowQuality")));
  !chooseNextRoad(Other).

// no suitable road, take first alternative
+!chooseNextRoad([]) 
: position(node(Pos)) & minRoadQuality(_) & destination(Dest) <-
  .nextSteps(Pos, Dest, [road(To, _)|_]);
  .logStep(choose(Pos,To,"unused","noRoadOfDesiredQuality"));
  !goto(To).

// simplest plan: always choose the "fastest" road
+!chooseNextRoad(Roads) 
: position(node(Pos)) & Roads = [road(NextStop, _)|_] <-
  .logStep(choose(Pos,NextStop,"fastestRoad"));
  !goto(NextStop).

// handle bridges first
+!goto(To)
: position(node(Pos)) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & waitForBridges <-
  .logStep(goto(Pos,To,"waiting"));
  .print("I have to wait for the bridge.").

+!goto(To)
: position(node(Pos)) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & not plannedRoute(_) <-
  .print("I would like to make a detour.");
  .getDetour(To, Detour);
  .logStep(goto(Pos,To,"bridge","neverWait",detour(Detour)));
  !useDetour(Detour).

+!goto(NextStop) : position(node(CurrentStop)) <-
  .logStep(move(CurrentStop,NextStop));
  +usedRoad(CurrentStop, NextStop);
  .switchRoad(CurrentStop, NextStop).

+!useDetour([]) <- .print("There is no route to use.").

+!useDetour(Route) : Route = [Next|More] <-
  -+plannedRoute(More);
  !goto(Next).
