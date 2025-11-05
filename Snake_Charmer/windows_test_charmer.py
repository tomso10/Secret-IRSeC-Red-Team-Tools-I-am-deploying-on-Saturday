import winrm
from requests_ntlm import HttpNtlmAuth

import winrm
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

def run_winrm_command(ip, username, password, command, use_ntlm=True, timeout=30):
    endpoint = f'http://{ip}:5985/wsman'  # change to https and 5986 if desired
    session = winrm.Session(endpoint, auth=(username, password), transport='ntlm' if use_ntlm else None)

    def _call():
        return session.run_cmd(command)  # no timeout kwarg here

    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_call)
        try:
            r = fut.result(timeout=timeout)  # enforce timeout here
        except FutureTimeoutError:
            # Attempt best-effort cleanup is difficult; just report timeout
            return {"ok": False, "status_code": None, "stdout": "", "stderr": "", "error": "operation timed out"}
        except Exception as e:
            return {"ok": False, "status_code": None, "stdout": "", "stderr": "", "error": str(e)}

    stdout = r.std_out.decode(errors="ignore") if r.std_out else ""
    stderr = r.std_err.decode(errors="ignore") if r.std_err else ""
    return {"ok": (r.status_code == 0), "status_code": r.status_code, "stdout": stdout, "stderr": stderr, "error": None}


res = run_winrm_command("172.16.118.133", "garrett", "garrett", "whoami")
if res["ok"]:
    print("SUCCESS:", res["stdout"])
else:
    print("FAILED:", res["error"] or res["stderr"])
