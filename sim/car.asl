nextStep(Next) :- position(P) & destination(D) & node(Next) & edge(P, Next) 
                  & .distance(Next, D, Dis1) & .distance(P, D, Dis2) & Dis1 < Dis2.

+step : position(Pos) & destination(Dest) & Pos \== Dest <-
  //-step?
  !reach(Dest).

+!reach(D) : position(D) <-
  .print("I have reached my destination").

+!reach(D) : nextStep(Next) <-
  .print("Moving to", Next);
  -+position(Next);
  !reach(D).

+!reach(D) <- .print("I have no idea what to do.").