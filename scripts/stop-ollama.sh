#!/bin/bash
# Ollama 停止脚本
pkill ollama && echo "Ollama 已停止" || echo "Ollama 未在运行"
