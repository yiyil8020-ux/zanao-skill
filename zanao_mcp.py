#!/usr/bin/env python3
"""赞哦 MCP Server 入口 → 委托到 scripts/zanao/mcp_server.py。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_server import run
run()
