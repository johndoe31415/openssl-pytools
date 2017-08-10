#!/usr/bin/python3
import re
import subprocess
import sys
import datetime

class BuildException(Exception): pass

class RestrictedBuilder(object):
    _DISABLEABLE_RE = re.compile("my @disablables = \((?P<text>.*?)\);",
            re.DOTALL)

    def __init__(self):
        self._logfile = open("../disableable.log", "a")

    def _git_clean(self):
        subprocess.check_call([ "git", "clean", "-dfx" ])

    def get_disableables(self):
        with open("Configure") as f:
            result = self._DISABLEABLE_RE.search(f.read())
            if result is None:
                raise Exception("Unable to determine disableables.")

        disableable = result.groupdict()["text"]
        disableable = disableable.replace("\n", " ")
        disableable = disableable.replace(",", " ")
        disableable = disableable.replace("\"", " ")
        disableable = set(disableable.split())
        disableable.remove("hw(-.+)?")
        return disableable

    def _log(self, msg):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("%s: %s" % (now, msg))
        print("%s: %s" % (now, msg), file = self._logfile)
        self._logfile.flush()

    def _try_buildstep(self, step, disableable, cmd):
        logfilename = "../dislog-%s-%s.log" % (disableable, step)
        with open(logfilename, "wb") as logfile:
            proc = subprocess.Popen(cmd, stdout = logfile,
                    stderr = subprocess.STDOUT)
            proc.wait()
            if proc.returncode != 0:
                raise BuildException("Build step %s-%s failed with return code %d."
                        % (step, disableable, proc.returncode))

    def _try_build_without(self, disableable):
        self._log("Trying building without %s..." % (disableable))
        self._git_clean()
        self._try_buildstep("config", disableable, [
            "./config", "no-%s" % (disableable), "-Werror"
        ])
        self._try_buildstep("make", disableable, [
            "make", "-j16"
        ])
        self._try_buildstep("test", disableable, [
            "make", "test"
        ])


    def run(self):
        for disableable in sorted(self.get_disableables()):
            try:
                self._try_build_without(disableable)
            except BuildException as e:
                self._log("%s failed: %s" % (disableable, str(e)))
            else:
                self._log("%s succeeded." % (disableable))

if (len(sys.argv) != 2) or (sys.argv[1] != "YES"):
    yn = input("This will git clean your repository. Type 'YES' to continue: ")
    if yn != "YES":
        print("Aborted.")
        sys.exit(1)

rb = RestrictedBuilder()
rb.run()


