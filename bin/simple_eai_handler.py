import os
import sys
import splunk.admin as admin

if sys.platform == "win32":
    import msvcrt
    # Binary mode is required for persistent mode on Windows.
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)


class EchoEAIHandler(admin.MConfigHandler):

    def setup(self):
        pass

    def handleList(self, confInfo):
        # confInfo is a mutable object; populate it with contents to display information in EAI output. Note that while
        # the interface is dictionary-like, confInfo is NOT a dictionary but an object of type ConfigInfo. A KeyError
        # will NOT be raised for the following operations.
        confInfo['stanza1']['attr'] = 'abcd'

admin.init(EchoEAIHandler, admin.CONTEXT_NONE)