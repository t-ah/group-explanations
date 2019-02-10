+step : position(Pos) & destination(Dest) & Pos \== Dest <-
  !reach(Dest).

+!reach(Dest) : onRoad <-
  -onRoad;
  .drive.

+!reach(Dest) : atIntersection(Node) & destination(Node) <-
  .print("I have reached my destination!");
  -destination(_).

+!reach(Dest) : atIntersection(Node) <-
  -atIntersection(_);
  .nextSteps(Node, Dest, Result); //[road(to,length),...] sorted by length
  !chooseNextRoad(Node, Result).

+!reach(Dest) <- .print("I have no idea what to do.").

// never take a road twice
+!chooseNextRoad(Pos, Roads)
: Roads = [road(To, _)|OtherRoads] & usedRoad(Pos, To) <-
  !chooseNextRoad(Pos, OtherRoads).

// take road quality into account
+!chooseNextRoad(Pos, Roads) // Roads = [road(To, _)|_]
: Roads = [road(To, _)|_] & minRoadQuality(Q) & edge(Pos, To, _, EdgeQ) & EdgeQ >= Q <-
  !goto(Pos, To).

// first element did not satisfy quality criterion
+!chooseNextRoad(Pos, Roads) : Roads = [_|Other] & minRoadQuality(_) <-
  !chooseNextRoad(Pos, Other).

// no suitable road, take first alternative
+!chooseNextRoad(Pos, []) : minRoadQuality(_) & destination(Dest) <-
  .nextSteps(Pos, Dest, [road(To, _)|_]);
  !goto(Pos, To).

// simplest plan: always choose the "fastest" road
+!chooseNextRoad(Pos, Roads) : Roads = [road(NextStop, _)|_] <-
  !goto(Pos, NextStop).


+!goto(CurrentStop, NextStop) <-
  +usedRoad(CurrentStop, NextStop);
  .switchRoad(CurrentStop, NextStop).