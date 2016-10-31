import os
import pexpect
import sys

class GromacsException(Exception):
    """
    An exception class to handle errors produced by calls to Gromacs.
    """
    pass

def default_synchronous_handler(
        terminal,
        responses = [],
        timeout=120,
        prompt=">>"):
    """
    Default Synchronous Handler
    ===========================

    This handler will store all terminal output and return it once the command
    has finished running.

    :param terminal: The pexpect terminal in which the command has been run
    :param responses: List of (question, answer) tuples, used to inject stdin
    :param timeout: Timeout in seconds between consecutive terminal outputs
    :param prompt: BaSH prompt string to expect after the command has finished.
    """
    output = []
    for question, answer in responses:
        terminal.expect(question)
        output.append(terminal.before + terminal.after)
        terminal.sendline(str(answer))
    while True:
        terminal.expect("\r\n", timeout=timeout)
        if prompt in terminal.before:
            all_output = "\n".join(output)
            if "error:" in all_output:
                raise GromacsException(all_output)
            return all_output
        output.append(terminal.before)

def gmx_verbose_handler(
        terminal,
        responses = [],
        timeout=120,
        prompt=">>"):
    """
    Verbose Synchronous Handler
    ===========================

    This handler will store all terminal output and return it once the command
    has finished running. Additionally the most recent line will be written to
    stdout.

    :param terminal: The pexpect terminal in which the command has been run
    :param responses: List of (question, answer) tuples, used to inject stdin
    :param timeout: Timeout in seconds between consecutive terminal outputs
    :param prompt: BaSH prompt string to expect after the command has finished.
    """
    output = []
    for question, answer in responses:
        terminal.expect(question)
        output.append(terminal.before + terminal.after)
        terminal.sendline(str(answer))
    while True:
        terminal.expect("[\n\r]", timeout=timeout)
        sys.stdout.write("\r"+terminal.before.strip())
        sys.stdout.flush()
        if prompt in terminal.before:
            sys.stdout.write("\r"+(" "*50)+"\r")
            all_output = "\n".join(output)
            if "error:" in all_output:
                raise GromacsException(all_output)
            return all_output
        output.append(terminal.before)

class GromacsCall(object):
    """
    Gromacs Call
    ============

    A single call to GROMACS (corresponding to a single command line call). This
    may be used multiple times if needed, but will always call the same command,
    from the same directory, with the same arguments.
    """
    def __init__(
            self,
            cwd,
            gromacs_path,
            module,
            arguments,
            gmx_gag=True):
        """
        Initialise
        ==========

        :param cwd: Working directory (relative or absolute) to call from
        :param gromacs_path: Path (or name) to use for GROMACS executable
        :param module: Name of GROMACS module to call
        :param arguments: List of arguments to pass to GROMACS
        :param gmx_gag: Add arguments to make GROMACS shut up
        """
        self.cwd = cwd
        self.gromacs_path = gromacs_path
        self.module = module
        self.arguments = arguments
        self.responses = []
        if gmx_gag:
            self.arguments.append("-noh")
            self.arguments.append("-noversion")
            self.arguments.append("-nocopyright")
    def call_string(self):
        """
        Call String
        ===========

        Returns the string required to perform the initial system call
        represented by this object.
        """
        call_str = self.gromacs_path
        call_str += " " + self.module + " "
        call_str += " ".join(self.arguments)
        return call_str
    def respond(self, question, answer):
        """
        Respond
        =======

        Adds an answer for expect to pass on seeing the question. This can be
        chained if needed.

        :param question: Regex to look for in STDOUT
        :param answer: String to pass via STDIN in response

        Example
        -------
        If GROMACS was going to ask (via STDOUT) "What is your name?" followed
        by "Hi [your name]. [GROMACS 'funny' quote]. What is your favourite
        colour?":

        gmx_call.respond(
            "What is your name\?",
            "Batman").respond(
            "Hi \w+\. .+\. What is your favourite colour\?",
            "Black"
            ).call()
        """
        self.responses.append((question, answer))
        return self
    def call(
            self,
            timeout=120,
            handler=default_synchronous_handler):
        """
        Call
        ====

        Spawns a bash terminal and runs this call in the terminal.

        Args:
          timeout (int): Timeout in seconds to allow between terminal responses
          handler (function): Handler to use to watch terminal output.

        Returns:
          Handler output.
        """
        bash_terminal = pexpect.spawn("/bin/bash")
        bash_terminal.sendline('cd ' + self.cwd)
        bash_terminal.sendline('export done="--done--"')
        bash_terminal.sendline('export PS1=">>>$done>>>\n"')
        bash_terminal.expect(">>>--done-->>>")
        bash_terminal.sendline(self.call_string())
        return handler(
            bash_terminal,
            timeout=timeout,
            responses=self.responses,
            prompt=">>>--done-->>>")


class Gromacs(object):
    """
    GROMACS Wrapper
    ===============

    A top-level object which creates function calls. All methods on the object,
    except for `cd`, result in a GROMACS call to the corresponding GROMACS
    module.

    Example
    -------

    Call `gmx mdrun`:

        gmx = Gromacs("/usr/bin/gmx")
        gmx.mdrun(deffnm="md", v=True).call()

    """
    def handler_function_closure(self, gmx_module):
        """
        Handler function for uncaught calls
        """
        def handler_function(_arguments=[], *args, **kwargs):
            if type(_arguments) is not list:
                _arguments = [_arguments]
            for key, val in kwargs.items():
                if not key.startswith("-"):
                    key = "-" + key
                if type(val) in [str, float, int]:
                    _arguments.append(key + " " + str(val))
                elif val is True:
                    _arguments.append(key)
            for arg in args:
                _arguments.append(arg)

            return GromacsCall(
                self.cwd,
                self.gromacs_path,
                gmx_module,
                _arguments
            )
        return handler_function
    def __init__(self, gromacs_path="gmx"):
        """
        Initialise
        ==========

        Args
          gromacs_path: Path to GROMACS installation, or alias or executable
        """
        self.gromacs_path = gromacs_path
        self.cwd = "."
    def cd(self, cwd="~"):
        """
        Change Directory
        ================

        Changes the GROMACS working directory to `cwd`.

        Args
          cwd: Working directory path
        """
        self.cwd = os.path.expanduser(cwd)
    def __getattr__(self, gmx_module):
        """
        To catch all calls other than cd and builtins
        """
        return self.handler_function_closure(gmx_module)
