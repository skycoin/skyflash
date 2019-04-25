# Windows standalone build tools

The windows app is generated with the pyinstaller tool inside a docker environment using wine: the linux windows emulator. But some bug on the UAC privilege escalation inside pyinstaller fails to generate a single .exe file with a correct UAC on it, instead we need to use a folder with the skyflash-gui.exe and all other files inside in which the UAC work flawlessly.

The tools design is a static .exe file so we took some design decision: The ingle file static app must be generated with a external tool, that tools need to be:

* Free software or at least a open source one.
* Can be used on linux to generate a windows exe via CLI scripts.

After some research we find the 7z tool from Igor Pavlov, a free software tool that allow us to accomplish out goal. In this folder there is two files that we used to generate the final static (portable) app.

## 7zSD.sfx

This is a modified variant of the 7z sfx module: the icon has been swapped with the project one. This is the windows extraction and exec tool.

## sfx_config.txt

This is the configuration file that will be embedded in the final app to customize the execution.
