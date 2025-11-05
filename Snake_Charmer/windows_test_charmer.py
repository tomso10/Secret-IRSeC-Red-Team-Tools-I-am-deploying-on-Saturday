import argparse

parser = argparse.ArgumentParser(description="Run a command on a host")
parser.add_argument("--ip", required=True, help="Target IP address")
parser.add_argument("--user", required=True, help="Username")
parser.add_argument("--passw", required=True, help="Password")
parser.add_argument("--cmd", required=True, help="Command to run")

args = parser.parse_args()

print("IP:", args.ip)
print("Username:", args.user)
print("Password:", args.passw)
print("Command:", args.cmd)
