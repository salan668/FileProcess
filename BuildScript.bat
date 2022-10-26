cd ..\..
d:
cd MyCode\Siemens\siemens-process
pyinstaller -D -w -c --distpath "D:\MyCode\Siemens\VidaProcess_V_0_1" --workpath "D:\MyCode\Siemens\build" --clean MainSpec.spec

拷贝Utility的dcm2niix.exe