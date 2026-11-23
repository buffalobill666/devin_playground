#!/usr/bin/env bash
# Git wrapper for this playground: safe.directory + PAT auth.
# PAT lives in github.pat (gitignored); it is passed per-command
# via http.extraHeader and never written into .git/config.
# Usage: ./gitpush.sh push | pull | fetch | status | ...
cd "$(dirname "$0")"
AUTH=$(echo -n "x-access-token:$(cat github.pat)" | base64 -w0)
GIT_TERMINAL_PROMPT=0 git -c safe.directory=F:/DEVIN_PLAYGROUND \
  -c credential.helper= \
  -c http.extraHeader="Authorization: Basic $AUTH" "$@"
