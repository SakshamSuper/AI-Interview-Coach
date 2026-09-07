# Data Structures and Algorithms

## Computational Complexity
Big-O notation describes the upper bound on time and space complexity in the worst-case scenario.
Common complexities: O(1) constant, O(log N) logarithmic, O(N) linear, O(N log N) linearithmic, O(N^2) quadratic, O(2^N) exponential.

## Hash Tables and Collision Resolution
Hash tables provide average O(1) lookup, insertion, and deletion.
Collisions occur when two keys produce the same hash index. Common resolution strategies:
1. Separate Chaining: Each bucket holds a linked list or balanced binary tree of colliding entries.
2. Open Addressing: Linear probing, quadratic probing, or double hashing to find an empty slot.

## Tree and Graph Traversals
- Depth-First Search (DFS): Explores as deep as possible along each branch before backtracking. Implemented with recursion or a stack. O(V + E).
- Breadth-First Search (BFS): Explores all neighbor nodes at current depth before moving deeper. Implemented using a queue. Finds shortest path in unweighted graphs. O(V + E).

## Dynamic Programming
Dynamic programming solves complex optimization problems by breaking them into overlapping subproblems and optimal substructure.
- Top-down with Memoization: Recursive approach storing computed subproblem answers.
- Bottom-up with Tabulation: Iterative approach filling a table starting from base cases.