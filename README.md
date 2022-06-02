# A Tiny Little Language

Programming languages aren't magical:
one piece of software translates text into instructions,
while another does what those instructions tell it to.
To explore how this works,
this repo contains implementsion of two complete (albeit very simple) languages.

## TLL

`tll.py` reads a JSON file from standard input and executes the program it represents.
Each command is stored as a list
that starts with the name of an instruction
and may contain Booleans, numbers, strings, or other lists (representing other instructions).
For example,
this program that starts with the number 1 and doubles it four times:

``` {: title="doubling.tll"}
[
    "seq",
    ["comment", "Double a number repeatedly"],
    ["array", "new", 10]
    ["set", "a", 1],
    ["print", "initial", ["get", "a"]],
    [
        "repeat",
        4,
        [
            "seq",
            ["set", "a", ["add", ["get", "a"], ["get", "a"]]],
	    ["if",
		["leq", ["get", "a"], 10],
		["print", "small", ["get", "a"]],
		["print", "large", ["get", "a"]]
	    ]
        ]
    ]
]
```

-   *Why JSON?*
    So we can parse the program with a single call to `json.load`.

-   *Why lists?*
    Because that's all a program is: a list of instructions,
    some of which are other lists of instructions.

-   *Why put the name of the instruction first?*
    To make it easy to find.
    Expressions like `2 + 3 * 5` take several dozen lines of code to parse
    because elements appear in mixed order
    and because we can't be sure what to do with one thing (like `+`)
    until we've seen a later thing (like `*`).

So how does TLL execute instructions?
First,
it defines one function for each instruction.
All of these functions take exactly the same parameters:
an *environment* (which is a dictionary containing all the program's variables)
and the instructions' arguments.
When given a list representing an instruction,
the function `do` uses the list's first element to figure out what other function to call
and calls it;
when given anything else, like a number or string,
`do` just returns that value immediately.

And that's pretty much it.
A function like `do_add` calls `do` to evaluate its arguments and then returns their sum;
a function like `do_seq` calls `do` once for each of its arguments in order
and returns the value of the last one;
`do_get` and `do_set` look up a variable's value and store new values respectively,
and `do_if` uses the result of evaluating its first argument
to decide whether to evaluate its second or third.
It's really that simple.

### Exercises

1.  Implement fixed-size one-dimensional arrays:
    `["array", "new", 10]` creates an array of 10 elements,
    while other instructions get and set particular array elements by index.

    - I made the `do_array` function. I'm not sure how to approach the second part though. Should I add another argument to specify the index? Or put the variable onto the list like the stack? 

2.  Add a `while` loop to TLL.

3.  The `"repeat"` instruction runs some other instruction(s) several times,
    but there is no way to access the loop counter inside those instructions.
    Modify `"repeat"` so that programs can do this.
    (Hint: allow people to create a new variable to hold the loop counter's current value.)

4.  Explain how the table `OPERATIONS` is constructed.

    - This is basically the same as the macro in C, a little different in its logic though. It looks for functions in the global scope (didn't know you could call .items in the globals function) if their name starts with "do_"

5.  Several of the instruction functions started with `assert` statements,
    which means that users get a stack trace of TLL itself
    when there's a bug in their program.
    1.  Define a new exception class called `TLLException`.
    2.  Write a utility function called `check`
        that raises a `TLLException` with a useful error message
        when there's a problem.
    3.  Add a `catch` statement to handle these errors.

6.  The docstring in each action function explain what it does.
    Can you rewrite those for `do_repeat` and `do_seq` to be clearer or more consistent?

## Defining and Calling Functions

TLL can do a lot:
in fact,
since it has variables, loops, and conditionals,
it can do everything that *any* programming language can do.
However,
writing TLL programs will be painful
because there's no way for users to define new operations within the language itself.
Doing this in `tllfunc.py` makes TLL less than 60 lines longer:

1.  Instead of using a single dictionary to store an environment
    we use a list of dictionaries.
    The first dictionary is the global environment;
    the others store variables belonging to active function calls.

2.  When we get or set a variable,
    we check the most recent environment first
    (i.e., the one that's last in the list);
    if the variable isn't there we look in the global environment.
    We *don't* look at the environments in between.

3.  A function definition looks like:

        ["def", "same", ["num"], ["get", "num"]]

    It has a name, a (possibly empty) list of parameter names,
    and a single instruction as a body
    (which will usually be a `"seq"` instruction).

4.  Functions are stored in the environment like any other value.
    The value stored for the function defined above would be:

        ["func", ["num"], ["get", "num"]]

    We don't need to store the name: that's recorded by the environment,
    just like it is for any other variable.

5.  A function call looks like:

        ["call", "same", 3]

    The values passed to the functions are normally expressions rather than constants,
    and are *not* put in a sub-list.
    The implementation:
    1.  Evaluates all of these expressions.
    2.  Looks up the function.
    3.  Creates a new environment whose keys are the parameters' names
        and whose values are the expressions' values.
    4.  Calls `do` to run the function's action and captures the result.
    5.  Discards environment created two steps previously.
    6.  Returns the function's result.

### Exercises

1.  Add a `--debug` command-line flag to `tllfunc.py`.
    When enabled, it makes TLL print a messages showing each function call and its result.

2.  Add a `"return"` instruction to TLL that ends a function call immediately
    and returns a single value.

3.  If you implemented arrays earlier,
    add variable-length parameter lists to TLL.

4.  `tllfunc.py` allows users to define functions inside functions.
    What variables can the inner function access when you do this?
    What variables *should* it be able to access?
    What would you have to do to enable this?

## Separating Compilation and Execution

You might feel there's still magic in TLL,
so let's build something lower-level.
Our virtual machine simulates a computer with three parts:

1.  An instruction pointer (IP)
    that holds the memory address of the next instruction to execute.
    It is automatically initialized to point at address 0,
    which is where every program must start.

1.  Four registers named R0 to R3 that instructions can access directly.
    There are no memory-to-memory operations in our VM:
    everything  happens in or through registers.

1.  256 words of memory, each of which can store a single value.
    Both the program and its data live in this single block of memory;
    we chose the size 256 so that each address will fit in a single byte.

The instructions for our VM are 3 bytes long.
The op code fits into one byte,
and each instruction may optionally include one or two single-byte operands.
Each operand is a register identifier,
a constant,
or an address
(which is just a constant that identifies a location in memory);
since constants have to fit in one byte,
the largest number we can represent directly is 256.
The table below uses the letters `r`, `c`, and `a`
to indicate instruction format:
`r` indicates a register identifier,
`c` indicates a constant,
and `a` indicates an address.

| Instruction | Code | Format | Action              | Example      | Equivalent              |
| ----------- | ---- | ------ | ------------------- | ------------ | ----------------------- |
|  `hlt`      |    1 | `--`   | Halt program        | `hlt`        | `sys.exit(0)`           |
|  `ldc`      |    2 | `rc`   | Load constant       | `ldc R0 123` | `R0 = 123`              |
|  `ldr`      |    3 | `rr`   | Load register       | `ldr R0 R1`  | `R0 = RAM[R1]`          |
|  `cpy`      |    4 | `rr`   | Copy register       | `cpy R0 R1`  | `R0 = R1`               |
|  `str`      |    5 | `rr`   | Store register      | `str R0 R1`  | `RAM[R1] = R0`          |
|  `add`      |    6 | `rr`   | Add                 | `add R0 R1`  | `R0 = R0 + R1`          |
|  `sub`      |    7 | `rr`   | Subtract            | `sub R0 R1`  | `R0 = R0 - R1`          |
|  `beq`      |    8 | `ra`   | Branch if equal     | `beq R0 123` | `if (R0 == 0) PC = 123` |
|  `bne`      |    9 | `ra`   | Branch if not equal | `bne R0 123` | `if (R0 != 0) PC = 123` |
|  `prr`      |   10 | `r-`   | Print register      | `prr R0`     | `print(R0)`             |
|  `prm`      |   11 | `r-`   | Print memory        | `prm R0`     | `print(RAM[R0])`        |

We put our VM's architectural details in `architecture.py`.
The VM itself is in `vm.py`:

-   The construct initializes the IP, the registers, and RAM.

-   `initialize` copies a program into RAM.
    A program is just a list of numbers;
    we'll see where they come from in a moment.

-   `fetch` gets the instruction that the IP refers to and moves the IP on to the next address.
    It then uses bitwise operations
    to extract the *op code* and operands from the instruction.

-   `run` is just a big switch statement
    that does whatever the newly-fetched instruction tells it to do,
    such copy a value from memory into a register
    or add the contents of two registers.
    The most interesting instructions are probably the branch instructions,
    which assign a new value to the IP
    so that execution continues at a different location in the program.

We could figure out numerical op codes by hand,
and in fact that's what the first programmers did.
However,
it's much easier to use an *assembler*,
which is just a small compiler for a language that very closely represents actual machine instructions.
Each command in our assembly languages matches an instruction in the VM.
Here's an assembly language program to print the value stored in R1 and then halt:

```{: title="print-r1.as"}
# Print initial contents of R1.
prr R1
hlt
```

In hexadecimal, its numeric representation is:

```{: title="print-r1.mx"}
00010a
000001
```

One thing the assembly language has that the instruction set doesn't
is labels on addresses.
The label `loop` doesn't take up any space;
instead,
it tells the assembler to give the address of the next instruction a name
so that we can refer to that address as `@loop` in jump instructions.
For example,
this program prints the numbers from 0 to 2

```{: title="count-up.as"}
# Count up to 3.
# - R0: loop index.
# - R1: loop limit.
ldc R0 0
ldc R1 3
loop:
prr R0
ldc R2 1
add R0 R2
cpy R2 R1
sub R2 R0
bne R2 @loop
hlt
```

Let's trace this program's execution:

1.  R0 holds the current loop index.
1.  R1 holds the loop's upper bound (in this case 3).
1.  The loop prints the value of R0 (one instruction).
1.  The program adds 1 to R0.
    This takes two instructions because we can only add register-to-register.
1.  It checks to see if we should loop again,
    which takes three instructions.
1.  If the program *doesn't* jump back, it halts.

The implementation of the assembler mirrors the simplicity of assembly language.
The main method gets interesting lines,
finds the addresses of labels,
and turns each remaining line into an instruction:
To find labels,
we go through the lines one by one
and either save the label *or* increment the current address
(because labels don't take up space).

To compile a single instruction we break the line into tokens,
look up the format for the operands,
and pack them into a single value;
combining op codes and operands into a single value
is the reverse of the unpacking done by the virtual machine.

It's tedious to write interesting programs when each value needs a unique name,
so we can add arrays to our assembler.
We allocate storage for arrays at the end of the program
by using `.data` on a line of its own to mark the start of the data section
and then `label: number` to give a region a name and allocate some storage space.

### Exercises

1.  Write an assembly language program that swaps the values in R1 and R2
    without affecting the values in other registers.

2.  Write an assembly language program that starts with
    the base address of an array in one word,
    the length of the array N in the next word,
    and N values immediately thereafter,
    and reverses the array in place.

3.  C stores character strings as non-zero bytes terminated by a byte containing zero.
    Write a program that starts with the base address of a string in R1
    and finishes with the length of the string (not including the terminator) in the same register.
