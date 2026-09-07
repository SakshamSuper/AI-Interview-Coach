# System Design and Distributed Systems Architecture

## Scalability and High Availability
Scalability refers to the ability of a system to handle increased load.
- Vertical Scaling (Scale-Up): Adding more compute/memory to a single server.
- Horizontal Scaling (Scale-Out): Adding more servers and distributing traffic via load balancers (Layer 4 TCP vs Layer 7 HTTP).

## CAP Theorem and Consistency Models
In distributed data stores, the CAP theorem states that a system can guarantee at most two of the following three:
1. Consistency (every read receives the most recent write or an error).
2. Availability (every non-failing node returns a response).
3. Partition Tolerance (the system continues to operate despite arbitrary message loss or network partitions).
Because network partitions are inevitable in distributed systems, real systems choose between CP (e.g., Spanner, Zookeeper) and AP (e.g., Cassandra, DynamoDB).

## Caching Strategies
- Cache-Aside (Lazy Loading): Application queries cache; if miss, queries database and writes to cache.
- Write-Through: Data is written into cache and database simultaneously.
- Write-Back (Write-Behind): Data written to cache first, asynchronously persisted to database.
- Eviction Policies: LRU (Least Recently Used), LFU (Least Frequently Used), FIFO.

## Message Queues and Event-Driven Architecture
Message queues like Apache Kafka and RabbitMQ decouple producers and consumers, absorb traffic spikes (backpressure), and enable asynchronous processing.
Kafka uses partitioned, append-only commit logs enabling high-throughput pub/sub and guaranteed message ordering per partition.