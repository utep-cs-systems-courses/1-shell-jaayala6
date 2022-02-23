#! /usr/bin/env python3

import os, sys, time, re, fileinput

def redirect(args):
    os.close(1)
    os.open(args[-1], os.O_CREAT | os.O_WRONLY)
    os.set_inheritable(1, True)
    os.execve(program, args[:-2], os.environ)
#-----------------------------------------
def pipe(args):
    splitArgs = args.index("|")
    arg1 = args[:splitArgs]
    arg2 = args[splitArgs+1:]

    pr,pw = os.pipe()

    for f in (pr, pw):
        os.set_inheritable(f, True)
    print("pipe fds: pr=%d, pw=%d" % (pr, pw))

    print("About to fork (pid=%d)" % pid)

    rc = os.fork()

    if rc < 0:
        print("fork failed, returning %d\n" % rc, file=sys.stderr)
        sys.exit(1)

    elif rc == 0:                   #  child - will write to pipe
        print("Child: My pid==%d.  Parent's pid=%d" % (os.getpid(), pid), file=sys.stderr)
        os.close(1)                 # redirect child's stdout
        os.dup(pw)
        for fd in (pr, pw):
            for dir in re.split(":", os.environ['PATH']): # try each directory in path
                program = "%s/%s" % (dir, args[0])
                try:
                    os.execve(program, arg1, os.environ)
                except FileNotFoundError:             # ...expected
                    pass
        print("hello from child")

    else:                           # parent (forked ok)
        print("Parent: My pid==%d.  Child's pid=%d" % (os.getpid(), rc), file=sys.stderr)
        os.close(0)
        os.dup(pr)
        for fd in (pw, pr):
            for dir in re.split(":", os.environ['PATH']): # try each directory in path
                program = "%s/%s" % (dir, args[0])
                try:
                    os.execve(program, arg2, os.environ)
                except FileNotFoundError:             # ...expected
                    pass                           #for line in fileinput.input():
        #   print("From child: <%s>" % line)
#-----------------------------------------
#original pid
pid = os.getpid()

#main shell
while 1:

    #print PS1
    cwd = re.split("/", os.getcwd())
    os.write(1, ("{"+os.environ['USER']+"@"+os.uname()[1]+" "+cwd[-1]+"}$ ").encode())

    #get user input/decode/split
    input = (os.read(0, 10000).strip()).decode()
    args = re.split(" ", input)

#-----------------------------------------
    if (args[0] == "exit"):
        sys.exit(420)
#-----------------------------------------
    if (args[0] == "cd"):
        try:
            if (len(args) < 2):
                os.chdir("/home/" + os.environ['USER'])
            else:
                os.chdir(args[1])
        except FileNotFoundError:
            pass
#-----------------------------------------
    else:
        rc = os.fork()
        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)
#-----------------------------------------
        elif rc == 0:                   # child

            os.write(1, ("Child: My pid==%d.  Parent's pid=%d\n" %
                 (os.getpid(), pid)).encode())

            for dir in re.split(":", os.environ['PATH']): # try each directory in path
                program = "%s/%s" % (dir, args[0])
                try:
                    if (len(args) < 2):
                        os.execve(program, args, os.environ) # try to exec program

                    elif ("|" in args):
                        pipe(args)

                    elif (">" in args):
                        redirect(args)

                    else:
                         os.execve(program, args, os.environ) # try to exec program

                except FileNotFoundError:             # ...expected
                    pass
            os.write(2, ("Child:    Could not exec %s\n" % args[0]).encode())
            sys.exit(1)                 # terminate with error
#-----------------------------------------
        else:                           # parent (forked ok)
            os.write(1, ("Parent: My pid=%d.  Child's pid=%d\n" %
                         (pid, rc)).encode())
            childPidCode = os.wait()
            os.write(1, ("Parent: Child %d terminated with exit code %d\n" %
                         childPidCode).encode())
