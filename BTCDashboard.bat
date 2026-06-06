@echo off
title BTC On-chain Dashboard
cd /d "%~dp0"
start http://localhost:8503
streamlit run app.py --server.port 8503
