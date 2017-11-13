echo off
cd %~dp0
RMDIR /Q /S %~dp0\dist
RMDIR /Q /S %~dp0\build
c:\Python36\python setup.py build
c:\Python36\python setup.py install
