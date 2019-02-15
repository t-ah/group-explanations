+destination(Dest) <- .print("I want to go to", Dest).

// is added before step; for cleaning up beliefs etc.
+beforeStep <-
  -position(_).

// step percept is added at the beginning of each simulation step
+step : destination(Dest) <-
  !reach(Dest).

+!reach(Dest) : position([N1,N2]) & edge(N1, N2, _, _) <-
  .takeRoad(N1, N2).

+!reach(Dest) : position(Node) & destination(Node) <-
  .logStep(reached(Node));
  .print("I have reached my destination!");
  -destination(_).

+!reach(Dest) : position(Node) & plannedRoute([NextStop|OtherStops]) <-
  .logStep(reach(NextStop, "partOfPlannedRoute"));
  -+plannedRoute(OtherStops);
  !goto(NextStop).

+plannedRoute([]) <- -plannedRoute(_).

+!reach(Dest) : position(Node) <-
  .logStep(reach("planNextStop", "noRoutePlanned"));
  .nextSteps(Node, Dest, Result); //[road(to,length),...] sorted by length
  !chooseNextRoad(Result).

+!reach(Dest) <- .print("I have no idea what to do.").

// never take a road twice
+!chooseNextRoad([road(To, _)|OtherRoads])
: position(Pos) & usedRoad(Pos, To) <-
  .logStep(choose(exclude(Pos,To,"used")));
  !chooseNextRoad(OtherRoads).

// take road quality into account
+!chooseNextRoad([road(To, _)|_])
: position(Pos) & minRoadQuality(Q) & edge(Pos, To, _, EdgeQ) & EdgeQ >= Q <-
  .logStep(choose(Pos,To,"unused","acceptQuality"));
  !goto(To).

// first element did not satisfy quality criterion
+!chooseNextRoad([First|Other])
: position(Pos) & minRoadQuality(_) <-
  .logStep(choose(Pos,First,"unused",discard("lowQuality")));
  !chooseNextRoad(Other).

// no suitable road, take first alternative
+!chooseNextRoad([]) 
: position(Pos) & minRoadQuality(_) & destination(Dest) <-
  .nextSteps(Pos, Dest, [road(To, _)|_]);
  .logStep(choose(Pos,To,"unused","noRoadOfDesiredQuality"));
  !goto(To).

// simplest plan: always choose the "fastest" road
+!chooseNextRoad([road(NextStop, _)|_])
: position(Pos) <-
  .logStep(choose(Pos,NextStop,"fastestRoad"));
  !goto(NextStop).

+!chooseNextRoad(_) <- .print("I failed to choose a road or I could not take my chosen road.").

// handle bridges first
+!goto(To)
: position(Pos) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & waitForBridges <-
  .logStep(goto(Pos,To,"waiting"));
  .print("I have to wait for the bridge.").

+!goto(To)
: position(Pos) & bridge(Pos, To) & .bridgeStatus(Pos, To, open(false)) & not plannedRoute(_) <-
  .print("I would like to make a detour.");
  .getDetour(To, Detour);
  .logStep(goto(Pos,To,"bridge","neverWait",detour(Detour)));
  !useDetour(Detour).

+!goto(NextStop) : position(CurrentStop) <-
  .logStep(move(CurrentStop,NextStop));
  +usedRoad(CurrentStop, NextStop);
  .takeRoad(CurrentStop, NextStop).

+!useDetour([]) <- .print("There is no route to use.").

+!useDetour(Route) : Route = [Next|More] <-
  -+plannedRoute(More);
  !goto(Next).