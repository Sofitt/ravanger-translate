#!/bin/bash
python3 scripts/json_to_modelfile.py
ollama rm saiga
ollama create saiga -f Modelfile
