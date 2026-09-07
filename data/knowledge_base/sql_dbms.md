# Relational DBMS and SQL Optimization

## ACID Properties of Database Transactions
1. Atomicity: All operations in a transaction succeed or all fail and roll back.
2. Consistency: Transactions transition the database from one valid state to another, maintaining constraints.
3. Isolation: Concurrent transactions do not interfere with each other. Isolation levels: Read Uncommitted, Read Committed, Repeatable Read, Serializable.
4. Durability: Once a transaction commits, changes survive even in system crashes.

## Indexing Mechanics and Query Optimization
B-Trees and B+ Trees are standard index structures for relational engines.
B+ Trees store all actual record pointers in leaf nodes connected by pointers, providing efficient range scans and O(log N) point lookups.
Common index anti-patterns:
- Applying functions or wildcards at the start of a column in WHERE clauses (WHERE LOWER(name) = 'foo' or WHERE name LIKE '%bar').
- Missing composite index ordering (Leftmost Prefix Rule).

## Database Normalization
- 1NF: Atomic column values, unique rows.
- 2NF: In 1NF and all non-key attributes are fully dependent on the primary key (no partial dependencies).
- 3NF: In 2NF and no transitive dependencies (non-key attributes dependent on other non-key attributes).