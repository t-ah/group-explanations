+step : position(Pos) & destination(Dest) & Pos \== Dest <-
  !reach(Dest).

+step : position(Pos) & destination(Dest) & Pos == Dest <-
  .print("I have reached my destination.");
  -destination(_).

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

//+!chooseNextRoad(Roads) : minRoadQuality(X) <-


// simplest plan: always choose the "fastest" road
+!chooseNextRoad(From, Roads) <-
  [Shortest|_] = Roads;
  road(NextNode, _) = Shortest;
  .switchRoad(From, NextNode).
