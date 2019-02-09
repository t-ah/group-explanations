+step : position(Pos) & destination(Dest) & Pos \== Dest <-
  !reach(Dest).

+!reach(Dest) : position(Dest) <-
  .print("I have reached my destination").

+!reach(Dest) : onRoad <-
  -onRoad;
  .print("driving");
  .drive.

+!reach(Dest) : atIntersection(Node) <-
  -atIntersection(_);
  .nextSteps(Node, Dest, Result); //[road(nr,length),...] sorted by length
  // TODO decide next road
  [Shortest|_] = Result;
  road(NextNode, _) = Shortest;
  .print("Going to", NextNode);
  .switchRoad(Node, NextNode).

+!reach(Dest) <- .print("I have no idea what to do.").