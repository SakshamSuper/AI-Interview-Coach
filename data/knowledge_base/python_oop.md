# Python Internals and Object-Oriented Programming

## Python Memory Management and the GIL
Python manages memory using private heap space containing all Python objects and data structures.
The Global Interpreter Lock (GIL) is a mutex that prevents multiple native threads from executing Python bytecodes at once in CPython.
To achieve true concurrency for CPU-bound tasks, developers use multiprocessing or C-extensions, whereas asyncio and threading work well for I/O-bound operations.

## Generators and Iterators
Generators produce values lazily using the yield keyword, saving substantial memory when processing large datasets.
An iterator implements __iter__() and __next__() protocols. When __next__() reaches the end, it raises StopIteration.

## Decorators
A decorator is a callable that takes another function as an argument, wraps it to extend or modify behavior, and returns the wrapper.
Common uses include logging, authentication, caching (e.g., unctools.lru_cache), and validation.

## SOLID Principles in Object-Oriented Design
1. Single Responsibility Principle (SRP): A class should have one, and only one, reason to change.
2. Open/Closed Principle (OCP): Software entities should be open for extension, but closed for modification.
3. Liskov Substitution Principle (LSP): Subtypes must be substitutable for their base types without altering correctness.
4. Interface Segregation Principle (ISP): Clients should not be forced to depend on methods they do not use.
5. Dependency Inversion Principle (DIP): High-level modules should not depend on low-level modules; both should depend on abstractions.