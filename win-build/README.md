# Windows standalone build tools

The windows app is generated with the pyinstaller tool inside a docker environment using wine: the linux windows emulator (see below for docker image details). But some bug on the UAC privilege escalation inside pyinstaller fails to generate a single .exe file with a correct UAC on it, instead we need to use a folder with the skyflash-gui.exe and all other files inside in which the UAC work flawlessly.

The tools design is a static .exe file so we took some design decision: The ingle file static app must be generated with a external tool, that tools need to be:

* Free software or at least a open source one.
* Can be used on linux to generate a windows exe via CLI scripts.

After some research we find the 7z tool from Igor Pavlov, a free software tool that allow us to accomplish out goal. In this folder there is two files that we used to generate the final static (portable) app.

## 7zSD.sfx

This is a modified variant of the 7z sfx module: the icon has been swapped with the project one. This is the windows extraction and exec tool.

## sfx_config.txt

This is the configuration file that will be embedded in the final app to customize the execution.

## Use of Docker to get a windows release file locally (Developers Only)

You can create the docker image to generate the Windows .exe file for testing purposes with the info in the [Docker](https://github.com/skycoin/skyflash/docker/win64py3/) folder, for the moment only the 64bits exe is generated.

To build the local Docker machine (suggested name is 'pyinstaller-win64py3:pyqt_winapi') you must have a functional docker install on your linux distro and run this command in the console *from the mentioned docker folder where the Dockerfile resides*:

```sh
docker build -t "pyinstaller-win64py3:pyqt_winapi" ./
```

The name is tied to the specific targets on the Makefile, so ***Do not change it*, to know more about it run `make help` in the root project folder

## Flash utility tool

The flashing on windows was a real challenge, as created and tested python3 code works ok, but not in threads, and we used a thread to get the UI responsive during the flash process, then some other options was tested and validated, some was a fail, some was ok but unstable... until we decide to create our own flashing tool: flash.py

The flash.py get compiled to a flash.exe CLI utility file in the deployment process and included in the portable app, it's main goal is to make the flash as a independent process thread and report back progress to the UI.
