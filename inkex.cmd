@ECHO OFF
REM Launch Inkscape extensions after setting PATH and PYTHONPATH
SETLOCAL
SET "PATH=%ProgramFiles%\Inkscape;%PATH%"
SET "PYTHONPATH=%APPDATA%\inkscape\extensions;%ProgramFiles%\Inkscape\share\extensions"
SET "_plugin=%~n1.py"
IF "%1" == "python" SET "_plugin="
IF "%1" == "debug" SET "_plugin="
IF "%1" == "" SET "_plugin="
IF "%_plugin%" == "" (
	python.exe %2 %3 %4 %5 %6 %7 %8 %9
) ELSE (
	SHIFT
	python.exe "%APPDATA%\inkscape\extensions\%_plugin%" %1 %2 %3 %4 %5 %6 %7 %8 %9
)
