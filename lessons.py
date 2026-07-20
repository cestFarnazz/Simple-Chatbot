# -*- coding: utf-8 -*-
# lessons.py — full version with detailed explanations and extra examples
# Each topic: level, text, code, exercise, answer, explain_answer

lessons = {
    # ----------------------------- Beginner level -----------------------------
    "Variables and Data Types": {
        "level": "Beginner",
        "text": """Variables are containers for holding data. In Python you don't need to
declare a variable's type in advance; the language engine infers the type
from the value you assign (Dynamic Typing).

Common types:
- int: whole numbers (e.g. 0, 10, -5)
- float: decimal numbers (e.g. 3.14, -0.001)
- str: text string (wrapped in ' ' or " ")
- bool: logical values True/False
- NoneType: the "nothing" value for absence of a value (None)

Key notes:
- A variable name must start with a letter or underscore (_) and contain no spaces.
- Python's naming convention for variables is snake_case (e.g. total_price).
- A variable's value can be changed while the program runs (mutable binding).""",
        "code": """# Defining and printing different data types
x = 10            # int
pi = 3.14159      # float
name = "Ali"      # str
is_active = True  # bool
nothing = None    # NoneType

print(type(x), type(pi), type(name), type(is_active), type(nothing))

# Type casting
age_str = "25"
age = int(age_str)      # '25' -> 25
height = float("1.82")  # '1.82' -> 1.82
print(age + 5, height + 0.18)

# Multiple assignment
a, b, c = 1, 2.5, "hello"
print(a, b, c)""",
        "exercise": "Create three variables name, age, and score; assign them a string, an integer, and a decimal respectively, and print them all with a single print call.",
        "answer": """name = "Sara"
age = 22
score = 95.5
print(name, age, score)""",
        "explain_answer": "Three variables of the appropriate types are defined and displayed together with one print call."
    },

    "Operators": {
        "level": "Beginner",
        "text": """Operators perform arithmetic, comparison, and logical operations.

Categories:
- Arithmetic: +, -, *, /, // (integer division), % (remainder), ** (power)
- Comparison: ==, !=, >, <, >=, <=
- Logical: and, or, not
- Compound assignment: +=, -=, *=, /=, ...

Note: division / always produces a float result; use // for integer division.""",
        "code": """a, b = 10, 3
print(a + b, a - b, a * b)
print(a / b, a // b, a % b, a ** b)

# Comparison
print(a == b, a != b, a > b, a <= b)

# Logical
x = 5
print(x > 0 and x < 10)  # between 0 and 10
print(not (x == 5))""",
        "exercise": "Define a number n such that its square is greater than 100, and show the check with a logical print.",
        "answer": """n = 11
print(n ** 2 > 100)""",
        "explain_answer": "With n=11, the square is 121, which is greater than 100; the comparison returns True."
    },

    "Conditionals (if/elif/else)": {
        "level": "Beginner",
        "text": """The conditional structure is used to make decisions based on conditions.
Multiple conditions can be chained with elif, and a default case can be
covered with else.

Note: indentation is meaningful in Python and defines blocks.""",
        "code": """x = int(7)
if x > 10:
    print("Greater than 10")
elif x == 10:
    print("Exactly 10")
else:
    print("Less than 10")

# Nested and compound conditions
age = 18
if 0 <= age <= 120:
    if age >= 18:
        print("Adult")
    else:
        print("Minor")
else:
    print("Invalid age")""",
        "exercise": "Write a program that prints 'Fizz' if the input number is a multiple of 3, 'Buzz' if a multiple of 5, and 'FizzBuzz' if both; otherwise print the number itself.",
        "answer": """n = 15
if n % 3 == 0 and n % 5 == 0:
    print("FizzBuzz")
elif n % 3 == 0:
    print("Fizz")
elif n % 5 == 0:
    print("Buzz")
else:
    print(n)""",
        "explain_answer": "The shared case (multiple of both 3 and 5) is checked first to avoid conflicting with the later conditions."
    },

    "The for Loop": {
        "level": "Beginner",
        "text": """The for loop iterates over sequences (lists, strings, range, etc.).
The range(start, stop, step) function is used to generate a numeric range.""",
        "code": """# Iterating over a range
for i in range(1, 6):
    print(i, end=" ")  # 1 2 3 4 5
print()

# Iterating over a list
names = ["Ali", "Sara", "Reza"]
for name in names:
    print("Hi", name)

# enumerate: getting index + value
for idx, name in enumerate(names, start=1):
    print(idx, name)""",
        "exercise": "Using for and range, compute and print the sum of the numbers 1 to 100.",
        "answer": """total = 0
for i in range(1, 101):
    total += i
print(total)""",
        "explain_answer": "The loop iterates from 1 to 100, and at each step the value of i is added to total."
    },

    "The while Loop": {
        "level": "Beginner",
        "text": """The while loop repeats as long as its condition holds.
Watch out for infinite loops; the condition must move toward False during execution.""",
        "code": """i = 5
while i > 0:
    print(i)
    i -= 1
print("Boom!")""",
        "exercise": "Use while to print the even numbers less than 10.",
        "answer": """i = 0
while i < 10:
    print(i)
    i += 2""",
        "explain_answer": "Starting from zero and incrementing by 2 at a time, only even numbers less than 10 are printed."
    },

    "Strings": {
        "level": "Beginner",
        "text": """Strings are sequences of characters. Common operations:
- Indexing and slicing (s[0], s[-1], s[2:5])
- Concatenation with + and repetition with *
- Key methods: upper/lower/strip/replace/split/join/startswith/endswith
- Formatting: f-strings, format()""",
        "code": """s = " Python 3.11 "
print(s.strip().upper())          # 'PYTHON 3.11'
print(s.replace("3.11", "3.12"))

# Slicing and indexing
t = "hello"
print(t[0], t[-1], t[1:4])        # h o ell

# f-string
name, score = "Sara", 97
print(f"Hello {name}, score={score}")""",
        "exercise": "Take a string and count how many times the letter 'a' appears in it.",
        "answer": """text = "banana"
count_a = text.count("a")
print(count_a)""",
        "explain_answer": "The count method on a string counts the occurrences of the given substring."
    },

    "Lists": {
        "level": "Beginner",
        "text": """Lists are mutable collections. Key methods:
append, extend, insert, pop, remove, index, sort, reverse, copy
Slicing operations like list slicing are also supported.""",
        "code": """nums = [3, 1, 4]
nums.append(1)
nums.extend([5, 9])
nums.sort()
print(nums)           # [1,1,3,4,5,9]

# Shallow copy
b = nums.copy()
b.pop()
print(nums, b)""",
        "exercise": "Create a list of grades and compute its average.",
        "answer": """scores = [18, 17.5, 19, 20]
avg = sum(scores) / len(scores)
print(avg)""",
        "explain_answer": "sum gives the total, and dividing by the list's length computes the average."
    },

    "Tuples and Sets (Tuple/Set)": {
        "level": "Beginner",
        "text": """Tuples are like lists but "immutable".
Sets remove duplicates and support set-theory operations: union, intersection, difference.""",
        "code": """t = (1, 2, 3)
# t[0] = 10  # error: a tuple cannot be modified

s1 = {1, 2, 3, 3}
s2 = {3, 4}
print(s1)            # {1,2,3}
print(s1 | s2)       # union
print(s1 & s2)       # intersection
print(s1 - s2)       # difference""",
        "exercise": "Build a set from the list [1,1,2,2,3] so it contains only unique elements.",
        "answer": """lst = [1,1,2,2,3]
unique = set(lst)
print(unique)""",
        "explain_answer": "Building a set from a list removes duplicate values."
    },

    "Dictionaries (Dict)": {
        "level": "Beginner",
        "text": """A dictionary is a mapping from key to value. The key must be hashable
(such as str, int, tuple).
Key methods: get, keys, values, items, update, pop.""",
        "code": """user = {"name": "Ali", "age": 21}
print(user.get("name"))
user["country"] = "IR"
for k, v in user.items():
    print(k, v)""",
        "exercise": "Create a dictionary with the keys name and age, and increment the age value by 1.",
        "answer": """person = {"name": "Sara", "age": 20}
person["age"] += 1
print(person)""",
        "explain_answer": "The numeric value of the 'age' key is incremented by one, and the structure is printed."
    },

    # ----------------------------- Intermediate level -----------------------------
    "Functions": {
        "level": "Intermediate",
        "text": """Functions are reusable units. Types of parameters:
- positional, keyword
- default values
- *args and **kwargs for a variable number of parameters
Return is used to hand back a result.""",
        "code": """def area(w, h=1):
    return w * h

print(area(5, 2))
print(area(5))              # h defaults to 1

def show(*args, **kwargs):
    print(args, kwargs)

show(1, 2, x=10, y=20)""",
        "exercise": "Write a function that computes the average of a variable number of input numbers (use *args).",
        "answer": """def avg(*nums):
    return sum(nums) / len(nums)

print(avg(1,2,3,4))""",
        "explain_answer": "*args collects the numbers into a tuple, and sum/len return the average."
    },

    "Variable Scope": {
        "level": "Intermediate",
        "text": """The LEGB Rule: Local, Enclosing, Global, Built-in.
Use the global and nonlocal keywords to modify outer variables.""",
        "code": """x = 10  # global

def outer():
    x = 20  # enclosing
    def inner():
        nonlocal x
        x += 1
        print("inner x:", x)
    inner()
    print("outer x:", x)

outer()
print("global x:", x)""",
        "exercise": "Write a function nested inside another function that uses nonlocal to increment a counter by one and print the new value.",
        "answer": """def outer():
    count = 0
    def inc():
        nonlocal count
        count += 1
        print(count)
    inc()

outer()""",
        "explain_answer": "With nonlocal, the enclosing function's local variable is modified, not a new one created."
    },

    "Error Handling (try/except)": {
        "level": "Intermediate",
        "text": """try/except is used to prevent a crash when an error occurs.
You can have multiple except blocks, along with else and finally blocks.""",
        "code": """try:
    x = int("12a")
    print("OK")
except ValueError:
    print("Invalid conversion")
else:
    print("No error")
finally:
    print("Always runs")""",
        "exercise": "Convert user input to int; if it fails, print an appropriate message.",
        "answer": """s = "123x"
try:
    n = int(s)
    print("Number:", n)
except ValueError:
    print("Invalid number")""",
        "explain_answer": "Whenever converting a string to a number isn't possible, a ValueError is raised and an appropriate message is printed."
    },

    "Reading and Writing Files": {
        "level": "Intermediate",
        "text": """with open safely opens a file and closes it automatically.
Modes: 'r' read, 'w' write (overwrite), 'a' append, 'b' binary.""",
        "code": """# Writing
with open("data.txt", "w", encoding="utf-8") as f:
    f.write("Hello\\nPython")

# Reading
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()
print(content)""",
        "exercise": "Create a file and write 3 lines to it; then read it and print the content.",
        "answer": """lines = ["first\\n", "second\\n", "third\\n"]
with open("out.txt", "w", encoding="utf-8") as f:
    f.writelines(lines)
with open("out.txt", "r", encoding="utf-8") as f:
    print(f.read())""",
        "explain_answer": "writelines writes several lines at once, then read reads back the entire content."
    },

    "Modules and Packages": {
        "level": "Intermediate",
        "text": """Every .py file is a module. A folder containing __init__.py is
considered a package.
import is used to reuse code. Use as for an alias and from to import a specific member.""",
        "code": """import math as m
from random import randint

print(m.sqrt(16))
print(randint(1, 3))""",
        "exercise": "Print today's date using the datetime module.",
        "answer": """from datetime import date
print(date.today())""",
        "explain_answer": "With from, only the needed member is imported, and then called."
    },

    "Object-Oriented Programming (basic class/inheritance)": {
        "level": "Intermediate",
        "text": """OOP is used to model real-world concepts. Key concepts: class, object,
attribute, method, inheritance.
__init__ is the constructor and self refers to the current instance.""",
        "code": """class Animal:
    def __init__(self, name):
        self.name = name
    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):
        return "Woof!"

d = Dog("Rex")
print(d.name, d.speak())""",
        "exercise": "Write a Rectangle class with width and height attributes and an area method.",
        "answer": """class Rectangle:
    def __init__(self, w, h):
        self.w = w
        self.h = h
    def area(self):
        return self.w * self.h

r = Rectangle(3,4)
print(r.area())""",
        "explain_answer": "__init__ sets up the attributes, and the area method returns the area."
    },

    "Recursion": {
        "level": "Intermediate",
        "text": """A recursive function is one that calls itself to solve a smaller
version of the same problem. Every recursive function needs:
- a base case that stops the recursion
- a recursive case that moves toward the base case

Caution: Python has a default recursion limit (usually 1000 calls deep);
very deep recursion raises a RecursionError. For simple counting or
summing tasks, a loop is often more efficient, but recursion is a natural
fit for problems with a repeating, self-similar structure (like tree
traversal).""",
        "code": """def factorial(n):
    if n <= 1:          # base case
        return 1
    return n * factorial(n - 1)  # recursive case

print(factorial(5))  # 120

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print([fibonacci(i) for i in range(7)])""",
        "exercise": "Write a recursive function that returns the sum of all numbers from 1 to n.",
        "answer": """def recursive_sum(n):
    if n <= 0:
        return 0
    return n + recursive_sum(n - 1)

print(recursive_sum(10))""",
        "explain_answer": "The base case is n <= 0, returning 0; otherwise the function adds n to the sum of everything below it, until the base case is reached."
    },

    "Regular Expressions": {
        "level": "Intermediate",
        "text": """The re module matches patterns in text. Key functions:
- re.match: checks for a match only at the start of the string
- re.search: finds the first match anywhere in the string
- re.findall: returns all non-overlapping matches as a list
- re.sub: replaces matches with another string

Patterns are usually written as raw strings (r"...") so backslashes
aren't interpreted by Python itself. Common tokens: \\d (digit), \\w (word
character), \\s (whitespace), + (one or more), * (zero or more).""",
        "code": """import re

text = "Order #1234 shipped on 2024-05-01, order #5678 pending"

# Find all order numbers
order_ids = re.findall(r"#(\\d+)", text)
print(order_ids)  # ['1234', '5678']

# Check if the text contains a date-like pattern
match = re.search(r"\\d{4}-\\d{2}-\\d{2}", text)
print(match.group() if match else "No date found")

# Replace all digits with 'X'
print(re.sub(r"\\d", "X", "abc123"))""",
        "exercise": "Use re.findall to extract every number from the string 'I have 3 cats, 12 fish, and 1 dog' and print the resulting list.",
        "answer": """import re
text = "I have 3 cats, 12 fish, and 1 dog"
numbers = re.findall(r"\\d+", text)
print(numbers)""",
        "explain_answer": "\\d+ matches one or more consecutive digits, so findall returns every number in the text as a list of strings."
    },

    "Raising Exceptions and Custom Exceptions": {
        "level": "Intermediate",
        "text": """Besides catching exceptions with except, you can raise them
yourself with raise — useful for rejecting invalid input early with a
clear error instead of letting the program fail confusingly later.

You can also define your own exception classes by inheriting from
Exception (or a more specific built-in exception). This lets calling
code catch your specific error type instead of a generic one.""",
        "code": """class NegativeNumberError(Exception):
    pass

def take_square_root(n):
    if n < 0:
        raise NegativeNumberError(f"Cannot take the square root of {n}")
    return n ** 0.5

try:
    take_square_root(-4)
except NegativeNumberError as e:
    print("Caught:", e)

print(take_square_root(16))""",
        "exercise": "Define a custom exception called EmptyListError, and write a function get_first(lst) that raises it if the list is empty; otherwise it returns the first element. Call it with an empty list inside a try/except and print the caught message.",
        "answer": """class EmptyListError(Exception):
    pass

def get_first(lst):
    if not lst:
        raise EmptyListError("The list is empty")
    return lst[0]

try:
    get_first([])
except EmptyListError as e:
    print("Caught:", e)""",
        "explain_answer": "The custom exception class carries a specific, descriptive name; raise triggers it manually when the list is empty, and except catches exactly that type."
    },

    "Type Hints": {
        "level": "Intermediate",
        "text": """Type hints (introduced in PEP 484) let you annotate the expected
types of function parameters and return values. Python remains
dynamically typed at runtime — hints are not enforced automatically —
but they make code more self-documenting and let editors/tools (like
mypy) catch type mistakes before running the code.

Syntax: `def f(x: int, y: str = "a") -> bool:`
For more complex types, use the typing module: List, Dict, Optional, Union.""",
        "code": """from typing import List

def total_price(prices: List[float], tax_rate: float = 0.1) -> float:
    subtotal = sum(prices)
    return subtotal * (1 + tax_rate)

print(total_price([10.0, 20.0, 5.0]))

def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("Sara"))""",
        "exercise": "Write a function named is_adult with a type-hinted parameter age: int and a return type of bool, that returns True if age is 18 or older. Call it with 20 and print the result.",
        "answer": """def is_adult(age: int) -> bool:
    return age >= 18

print(is_adult(20))""",
        "explain_answer": "The `age: int` hint documents the expected parameter type, and `-> bool` documents the return type; Python still runs the function normally regardless of the hints."
    },

    "Virtual Environments and pip": {
        "level": "Intermediate",
        "text": """A virtual environment is an isolated, per-project Python installation,
so each project can have its own package versions without conflicting
with other projects or the system-wide Python.

Typical commands (run in your terminal, not inside a Python script):
- `python -m venv venv` — create a virtual environment named "venv"
- `venv\\Scripts\\activate` — activate it on Windows
- `source venv/bin/activate` — activate it on macOS/Linux
- `pip install <package>` — install a package into the active environment
- `pip freeze > requirements.txt` — save the exact installed versions
- `pip install -r requirements.txt` — install everything listed in that file

From within a running Python script, you can check whether you're
currently inside a virtual environment by comparing sys.prefix (the
active environment's path) to sys.base_prefix (the system Python's path);
they're equal outside a virtual environment and different inside one.""",
        "code": """import sys

in_virtual_env = sys.prefix != sys.base_prefix
print("Running inside a virtual environment:", in_virtual_env)
print("Python executable:", sys.executable)""",
        "exercise": "Write a script that prints whether the current interpreter is running inside a virtual environment (compare sys.prefix to sys.base_prefix).",
        "answer": """import sys
print(sys.prefix != sys.base_prefix)""",
        "explain_answer": "sys.prefix points to the currently active environment; sys.base_prefix points to the underlying system installation. They differ only when a virtual environment is active."
    },

    # ----------------------------- Advanced level -----------------------------
    "List Comprehensions": {
        "level": "Advanced",
        "text": """List comprehensions are a compact syntax for building a new list from
a sequence. A condition can also be added.""",
        "code": """nums = [1,2,3,4,5]
squares = [x*x for x in nums]
evens = [x for x in nums if x % 2 == 0]
print(squares, evens)""",
        "exercise": "Build a list of the cubes of numbers 1..5, including only the odd ones.",
        "answer": """cubes_odd = [x**3 for x in range(1,6) if x % 2 == 1]
print(cubes_odd)""",
        "explain_answer": "The if condition at the end of the comprehension selects the odd elements."
    },

    "Decorators": {
        "level": "Advanced",
        "text": """A decorator is a function that takes another function and extends its
behavior without changing its body.
Basic pattern: a decorator factory function that returns a wrapper.""",
        "code": """def logger(func):
    def wrapper(*args, **kwargs):
        print("calling", func.__name__)
        result = func(*args, **kwargs)
        print("done")
        return result
    return wrapper

@logger
def add(a,b):
    return a+b

print(add(2,3))""",
        "exercise": "Write a decorator that measures a function's execution time (use time.time).",
        "answer": """import time
def timed(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print("elapsed:", end-start)
        return result
    return wrapper

@timed
def work():
    sum(range(10_0000))

work()""",
        "explain_answer": "The time is recorded before and after the function runs, and the difference is printed; the decorator injects this behavior.",
        # The elapsed value differs on every run (it's a real time measurement),
        # so it must be masked before comparing output — otherwise even the
        # correct reference answer wouldn't match itself.
        "mask_patterns": [r"elapsed: [0-9.eE+-]+"],
    },

    "Generators and Iterators": {
        "level": "Advanced",
        "text": """A generator uses yield to lazily produce a sequence. Benefit: lower
memory usage.
Every generator is an iterator.""",
        "code": """def countdown(n):
    while n > 0:
        yield n
        n -= 1

for x in countdown(3):
    print(x)""",
        "exercise": "Write a generator that produces only the even numbers up to n.",
        "answer": """def even_gen(n):
    for i in range(0, n+1, 2):
        yield i

print(list(even_gen(10)))""",
        "explain_answer": "With a step of 2, only even numbers are produced; converted to a list for quick viewing."
    },

    "Working with JSON": {
        "level": "Advanced",
        "text": """The json library serializes/deserializes data (dict/list/...) to and
from a JSON string.""",
        "code": """import json
data = {"name":"Ali","scores":[18,19]}
s = json.dumps(data, ensure_ascii=False)  # to string
print(s)
back = json.loads(s)                      # to a Python structure
print(back["name"])""",
        "exercise": "Create a student dictionary (name, age), convert it to JSON, and print it.",
        "answer": """import json
student = {"name":"Sara","age":20}
print(json.dumps(student, ensure_ascii=False))""",
        "explain_answer": "dumps converts a Python structure into a JSON string; ensure_ascii=False preserves non-ASCII characters."
    },

    "SQLite (lightweight database)": {
        "level": "Advanced",
        "text": """sqlite3 is a built-in module for a file-based database. Good for
portfolio projects and small apps.""",
        "code": """import sqlite3

conn = sqlite3.connect(":memory:")
cur = conn.cursor()
cur.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT)")
cur.execute("INSERT INTO users(name) VALUES (?)", ("Ali",))
conn.commit()
cur.execute("SELECT * FROM users")
print(cur.fetchall())
conn.close()""",
        "exercise": "Create a table named students with id and name columns, insert one record, and read it back.",
        "answer": """import sqlite3
conn = sqlite3.connect(":memory:")
c = conn.cursor()
c.execute("CREATE TABLE students(id INTEGER PRIMARY KEY, name TEXT)")
c.execute("INSERT INTO students(name) VALUES (?)", ("Sara",))
conn.commit()
c.execute("SELECT * FROM students")
print(c.fetchall())
conn.close()""",
        "explain_answer": "After creating the table and inserting a record, the data is fetched with SELECT and the connection is closed at the end."
    },

    "Threading": {
        "level": "Advanced",
        "text": """Thread is useful for doing concurrent I/O-bound work.
For CPU-bound work, multiprocessing is preferable (because of the GIL).""",
        "code": """import threading, time

def worker(n):
    print("start", n)
    time.sleep(1)
    print("end", n)

threads = []
for i in range(3):
    t = threading.Thread(target=worker, args=(i,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
print("done")""",
        "exercise": "Create two threads that each sleep for 2 seconds and then print a message; finally print 'All done'.",
        "answer": """import threading, time

results = []

def job(name):
    time.sleep(2)
    results.append(name)

t1 = threading.Thread(target=job, args=("A",))
t2 = threading.Thread(target=job, args=("B",))
t1.start(); t2.start()
t1.join(); t2.join()

for name in sorted(results):
    print(name, "finished")
print("All done")""",
        "explain_answer": "Both threads run concurrently and each append their name to a shared list once done; sorting before printing keeps the output order deterministic regardless of which thread happens to finish first."
    },

    "Tkinter (GUI basics)": {
        "level": "Advanced",
        "text": """Tkinter is the built-in library for building simple user interfaces.
Concepts: the main window, widgets (Label/Button/Entry/Text), layout with pack/grid/place.""",
        "code": """import tkinter as tk

root = tk.Tk()
root.title("Hello")
label = tk.Label(root, text="Hello Tkinter")
label.pack(padx=10, pady=10)
btn = tk.Button(root, text="Quit", command=root.destroy)
btn.pack(pady=5)
root.mainloop()""",
        "exercise": "Create a window with an Entry and a Button so that the input text is shown in a Label.",
        "answer": """import tkinter as tk
def show():
    lbl.config(text=ent.get())

root = tk.Tk()
ent = tk.Entry(root)
ent.pack()
btn = tk.Button(root, text="Show", command=show)
btn.pack()
lbl = tk.Label(root, text="")
lbl.pack()
root.mainloop()""",
        "explain_answer": "The button click event calls the show function and puts the Entry's text into the Label.",
        # This is a GUI exercise: root.mainloop() blocks forever and never
        # produces comparable stdout; auto-grading doesn't make sense for it.
        "auto_gradable": False,
    },

    "Custom Context Managers": {
        "level": "Advanced",
        "text": """The `with` statement calls two special (dunder) methods on an object:
`__enter__` (when entering the block) and `__exit__` (when leaving it,
even if an exception occurred). Writing your own context manager class
lets you guarantee setup/cleanup code always runs — useful for things
like opening/closing resources, timing a block, or temporarily changing
settings.

A simpler alternative is the `@contextlib.contextmanager` decorator on a
generator function, using `yield` to mark the boundary between setup and
teardown.""",
        "code": """class Timer:
    def __enter__(self):
        import time
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        import time
        elapsed = time.time() - self.start
        print("Block finished")
        return False  # don't suppress exceptions

with Timer() as t:
    total = sum(range(1000))

print(total)""",
        "exercise": "Write a context manager class called Announcer whose __enter__ prints 'Entering' and whose __exit__ prints 'Exiting'. Use it in a with block that just passes, and observe the print order.",
        "answer": """class Announcer:
    def __enter__(self):
        print("Entering")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Exiting")
        return False

with Announcer():
    pass""",
        "explain_answer": "__enter__ runs when the with block starts and __exit__ runs when it ends, regardless of what happens inside the block."
    },

    "Unit Testing (unittest)": {
        "level": "Advanced",
        "text": """The unittest module (built into Python) lets you write automated
tests that verify your code behaves as expected. A test is a method on a
class inheriting from unittest.TestCase, using assertion methods like
assertEqual, assertTrue, assertRaises.

Writing tests catches bugs early and documents how your code is meant to
behave — this entire chatbot project itself is built and verified with
this same approach.""",
        "code": """import io
import unittest

def add(a, b):
    return a + b

class TestAdd(unittest.TestCase):
    def test_add_positive_numbers(self):
        self.assertEqual(add(2, 3), 5)

    def test_add_negative_numbers(self):
        self.assertEqual(add(-1, -1), -2)

suite = unittest.TestLoader().loadTestsFromTestCase(TestAdd)
runner = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0)
result = runner.run(suite)
print("All tests passed:", result.wasSuccessful())""",
        "exercise": "Write a unittest.TestCase that checks a function multiply(a, b) returns the correct product for 3 and 4, run it, and print whether all tests passed.",
        "answer": """import io
import unittest

def multiply(a, b):
    return a * b

class TestMultiply(unittest.TestCase):
    def test_multiply(self):
        self.assertEqual(multiply(3, 4), 12)

suite = unittest.TestLoader().loadTestsFromTestCase(TestMultiply)
runner = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0)
result = runner.run(suite)
print("All tests passed:", result.wasSuccessful())""",
        "explain_answer": "The TestCase's assertEqual checks the actual result against the expected one; running the suite through a TextTestRunner (with its default output redirected to an in-memory stream) keeps stdout clean, showing only our own summary line."
    },
}
