#!/usr/bin/env python3
"""赞哦 token 自动刷新入口 → 委托到 scripts/zanao/token_tools.py。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from token_tools import main
main()
