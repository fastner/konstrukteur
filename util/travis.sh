#!/bin/bash

echo ">>> PREPARING ENVIRONMENT..."
cd bin || exit 1
if ! [ `which python3` ]; then
  ln -sf `which python` python3 || exit 1 
fi
export PATH="`pwd`:$PATH"; 
cd .. || exit 1

echo
echo ">>> EXECUTING JASY VERSION..."
konstrukteur --version || exit 1

echo
echo ">>> RUNNING JASY CREATE"
konstrukteur create --name mytest || exit 1

echo
echo ">>> EXECUTING BUILD STEP..."
cd mytest || exit 1
konstrukteur || exit 1
cd .. || exit1
rm -rf mytest || exit1

echo 
echo ">>> DONE - ALL FINE"