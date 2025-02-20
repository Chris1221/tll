"""A tiny little language in one file."""

import json
import sys


def do_add(env, args):
    """Add two values.

    ["add" A B] => A + B
    """
    assert len(args) == 2
    left = do(env, args[0])
    right = do(env, args[1])
    return left + right


def do_comment(env, args):
    """Ignore instructions.

    ["comment" "text"] => None
    """
    return None


def do_get(env, args):
    """Get the value of a variable.

    ["get" name] => env{name}
    """
    assert len(args) == 1
    assert args[0] in env, f"Unknown variable {args[0]}"

    # get the index of the variable 
    # then retrieve the variable
    idx = env[args[0]]


    assert "stack" in env, "stack not found, initialize array first"
    return env['stack'][idx]


def do_gt(env, args):
    """Strictly greater than.

    ["gt" A B] => A > B
    """
    assert len(args) == 2
    return do(env, args[0]) > do(env, args[1])


def do_if(env, args):
    """Make a choice: only one sub-expression is evaluated.

    ["if" C A B] => A if C else B
    """
    assert len(args) == 3
    cond = do(env, args[0])
    choice = args[1] if cond else args[2]
    return do(env, choice)


def do_leq(env, args):
    """Less than or equal.

    ["leq" A B] => A <= B
    """
    assert len(args) == 2
    return do(env, args[0]) <= do(env, args[1])


def do_neg(env, args):
    """Arithmetic negation.

    ["neq" A] => -A
    """
    assert len(args) == 1
    return -do(env, args[0])


def do_not(env, args):
    """Logical negation.

    ["not" A] => not A
    """
    assert len(args) == 1
    return not do(env, args[0])


def do_or(env, args):
    """Logical or.
    The second sub-expression is only evaluated if the first is false.

    ["or" A B] => A or B
    """
    assert len(args) == 2
    if temp := do(env, args[0]):
        return temp
    return do(env, args[1])


def do_print(env, args):
    """Print values.

    ["print" ...values...] => None # print each value
    """
    args = [do(env, a) for a in args]
    print(*args)
    return None


def do_repeat(env, args):
    """Repeat instructions some number of times.

    name is the name of the counter variable

    ["repeat" N expr name] => expr # last one of N
    """
    assert len(args) == 3
    count = do(env, args[0])
    for i in range(count):
        result = do(env, args[1])
        result = do(env, ["set", args[2], i])
    return result


def do_seq(env, args):
    """Do a sequence of operations.

    ["seq" A B...] => last expr # execute in order
    """
    for a in args:
        result = do(env, a)
    return result

def do_array(env, args):
    """Makes a fixed-size 1D array.

    ["array" name length] => [0, ..., 0] 
    """
    assert len(args) == 2 # need both name and length
    name = do(env, args[0])
    count = do(env, args[1])

    if name == "new":
        env["stack"] = [None] * count # this is a list, not a fixed-size array....
        env["ip"] = 0 # instruction pointer, like in the book
    else:
        raise NotImplementedError("array name must be 'new'")


def do_set(env, args):
    """Assign to a variable.

    ["seq" name expr] => expr # and env{name} = expr
    """
    assert len(args) == 2
    assert isinstance(args[0], str)
    name = do(env, args[0])
    value = do(env, args[1])

    assert "stack" in env, "stack not found, initialize array first"
    env["stack"][env["ip"]] = value
    
    # Store the current position as the index of the variable
    env[args[0]] = env["ip"]

    # Then increment the index
    env["ip"] += 1


    return value


# Lookup table of operations.
OPERATIONS = {
    name.replace("do_", ""): func
    for (name, func) in globals().items()
    if name.startswith("do_")
}


def do(env, instruction):
    """Run the given instruction in the given environments."""
    if not isinstance(instruction, list):
        return instruction
    op, args = instruction[0], instruction[1:]
    assert op in OPERATIONS
    return OPERATIONS[op](env, args)


if __name__ == "__main__":
    program = json.load(sys.stdin)
    result = do({}, program)
    print("=>", result)
