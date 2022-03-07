#! /usr/bin/env python3

import os, sys, time, re, fileinput

def redirect(args):
    #close fd 1
    os.close(1)
    #open path specified after >
    os.open(args[-1], os.O_CREAT | os.O_WRONLY)
    #inherit with 1
    os.set_inheritable(1, True)
    #execute program minus the last 2 args (> "PATH TO FILE")
    os.execve(program, args[:-2], os.environ)


def redirect2(args):
    #close fd 0
    os.close(0)
    #open path specified after <
    os.open(args[-1], os.O_RDONLY)
    #inherit with 0
    os.set_inheritable(0, True)
    #execute program minus the last 2 args (> "PATH TO FILE")
    os.execve(program, args[:-2], os.environ)

#-----------------------------------------
def pipe(args):
    splitArgs = args.index("|")
    arg1 = args[:splitArgs]
    arg2 = args[splitArgs+1:]

    pr,pw = os.pipe()

    #print("pipe fds: pr=%d, pw=%d" % (pr, pw))

    #print("About to fork (pid=%d)" % pid)

    rc_p = os.fork()

    if rc_p < 0:
        #print("fork failed, returning %d\n" % rc_p, file=sys.stderr)
        sys.exit(1)

    elif rc_p == 0:                   #  child - will write to pipe
        #print("Child: My pid==%d.  Parent's pid=%d" % (os.getpid(), pid), file=sys.stderr)
        os.close(1)                 # redirect child's stdout
        os.dup(pw)
        os.set_inheritable(1, True)
        for fd in (pr, pw):
            for dir in re.split(":", os.environ['PATH']): # try each directory in path
                program = "%s/%s" % (dir, arg1[0])
                try:
                    os.execve(program, arg1, os.environ)
                except FileNotFoundError:             # ...expected
                    pass
        #print("hello from child")

    else:                           # parent (forked ok)
        rc_p2 = os.fork()

        if rc_p2 < 0:
            sys.exit(1)

        elif rc_p2 == 0:
            #print("Parent: My pid==%d.  Child's pid=%d" % (os.getpid(), rc_p), file=sys.stderr)
            os.close(0)
            os.dup(pr)
            os.set_inheritable(0, True)
            for fd in (pw, pr):
                for dir in re.split(":", os.environ['PATH']): # try each directory in path
                    program = "%s/%s" % (dir, arg2[0])
                    try:
                        os.execve(program, arg2, os.environ)
                    except FileNotFoundError:             # ...expected
                        pass    #for line in fileinput.input():
        #   print("From child: <%s>" % line)
        else:
            childPidCode = os.wait()
        for fd in (pr, pw):
            os.close(fd)
        childPidCode = os.wait()
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
    elif (args[0] == "cd"):
        try:
            if (len(args) < 2):
                os.chdir("/home/" + os.environ['USER'])
            else:
                os.chdir(args[1])
        except FileNotFoundError:
            pass
#-----------------------------------------
    elif ("|" in args):
        pipe(args)
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

                    if (">" in args):
                        redirect(args)

                    elif ("<" in args):
                        redirect2(args)

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



#pipe call fork twice for each side of pipe
#
