#!/bin/bash
source ~/.bashrc; cd /gloome/; module load mamba/mamba-1.5.8; mamba activate /gloome/gloome_env2/; python /gloome/app/runs_automatic_report_sending.py;