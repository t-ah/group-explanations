!init.

+!init <-
  .perceive;
  name(N);
  .print("Hello, I am ", N);
  destination(D);
  position(P);
  .print("My goal is to go from", P, "to", D);
  !reach(D).

+!reach(D) : position(D) <-
  .print("I have reached my destination").

+!reach(D) : position(P) & destination(D) & node(Next) & edge(P, Next)
            & .distance(Next, D, Dis1) & .distance(P, D, Dis2) & Dis1 < Dis2 <-
  .print("Moving from", P, "to", Next);
  -+position(Next);
  !reach(D).

+!reach(D) <- .print("I have no idea what to do.").