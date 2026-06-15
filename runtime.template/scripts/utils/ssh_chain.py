#!/usr/bin/env python3
"""ssh_chain.py - 按 hosts 链式 SSH 检查和执行工具。

用法:
    python ssh_chain.py check <hosts_file>
    python ssh_chain.py exec <hosts_file> <command>
"""

import json
import subprocess
import sys
from pathlib import Path


def check_host(host_config: dict) -> dict:
    """检查单个 host 的 SSH 连通性。"""
    host = host_config.get("host", "")
    port = host_config.get("port", 22)
    user = host_config.get("user", "")
    key = host_config.get("keyPath", "")

    cmd = ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes"]
    if key:
        cmd.extend(["-i", key])
    cmd.extend(["-p", str(port), f"{user}@{host}", "echo ok"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return {
            "host": host,
            "reachable": result.returncode == 0,
            "error": result.stderr.strip() if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {"host": host, "reachable": False, "error": "timeout"}
    except Exception as e:
        return {"host": host, "reachable": False, "error": str(e)}


def check_chain(hosts_file: str) -> list:
    """检查整条 host 链。"""
    hosts = json.loads(Path(hosts_file).read_text(encoding="utf-8"))
    results = []
    for h in hosts:
        results.append(check_host(h))
    return results


def execute_chain(hosts_file: str, command: str) -> str:
    """在链上执行命令 (通过最后一个 host)。"""
    hosts = json.loads(Path(hosts_file).read_text(encoding="utf-8"))
    last = hosts[-1]
    port = last.get("port", 22)
    user = last.get("user", "")
    key = last.get("keyPath", "")

    cmd = ["ssh", "-o", "BatchMode=yes"]
    if key:
        cmd.extend(["-i", key])
    cmd.extend(["-p", str(port), f"{user}@{last['host']}", command])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return result.stdout


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: ssh_chain.py [check|exec] <hosts_file> [command]", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    hosts_file = sys.argv[2]

    if action == "check":
        results = check_chain(hosts_file)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif action == "exec":
        command = sys.argv[3] if len(sys.argv) > 3 else "echo hello"
        output = execute_chain(hosts_file, command)
        print(output)
