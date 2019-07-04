.DEFAULT_GOAL := help

.PHONY : deps clean build

PWD = $(shell pwd)
PWDWIN = $(shell pwd)/win-build

deps: ## Install all the needed deps to build it in Ubuntu 18.04 LTS and alike
	sudo apt update -q
	sudo apt install -y python3 python3-all python3-pip python3-pyqt5 python3-pyqt5.qtquick qml-module-qtquick2 qml-module-qtquick-window2 qml-module-qtquick-layouts qml-module-qtquick-extras qml-module-qtquick-dialogs qml-module-qtquick-controls qml-module-qt-labs-folderlistmodel qml-module-qt-labs-settings fakeroot python3-stdeb p7zip-full make
	pip3 install setuptools pyqt5 PyInstaller requests

deps-windows: deps ## Installs a docker image to build the windows .exe from inside linux
	# remove the old image from past dev envs
	-sudo docker image rm pyinstaller-win64py3:pyqt_winapi
	-sudo docker image rm pyinstaller-win64py3:skyflash
	# install docker
	sudo apt install apt-transport-https ca-certificates curl software-properties-common
	curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
	sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
	sudo apt update -q
	apt-cache policy docker-ce
	sudo apt install docker-ce
	# add your user to docker group
	sudo usermod -aG docker ${USER}
	# build the docker image
	cd docker/win64py3 && docker build -t "pyinstaller-win64py3:skyflash" ./
	###############################################################################################
	##### If this last step failed, please logout/login and try again, it must work this time" ####
	###############################################################################################

init: clean ## Initial cleanup, erase even the final app dir
	-rm -rdf final
	-mkdir final

clean: ## Clean the environment to have a fresh start
	-sudo rm -rdf skyflash.egg-info
	-sudo rm -rdf deb_dist
	-sudo rm -rdf dist
	-sudo rm -rdf build
	-sudo rm -rdf __pycache__
	-sudo rm -rdf skyflash/__pycache__
	-sudo rm skyflash-*.tar.gz
	-sudo rm -rdf win-build/dist
	-sudo rm -rdf win-build/build
	-sudo rm -rdf win-build/__pycache__
	-sudo rm -rdf posix-build/dist
	-sudo rm -rdf posix-build/build
	-sudo rm -rdf posix-build/__pycache__

build: clean ## Build the pip compatible install file
	python3 setup.py build
	python3 setup.py sdist
	mv dist/skyflash-*.tar.gz final/
	ls -lh final/

install: build ## Install the built pip file
	sudo python3 setup.py install

win-flasher: ## Create the flasher tool for windows (for travis only)
	cd win-build && docker run --rm -v "$(PWDWIN):/src/" cdrx/pyinstaller-windows

win-flasher-dev: ## Create the flasher tool for windows (no internet needed if you run "make deps-windows" already)
	cd win-build && docker run --rm -v "$(PWDWIN):/src/" pyinstaller-win64py3:skyflash

win: clean win-flasher ## Create a windows static app (for travis only)
	docker run --rm -v "$(PWD):/src/" cdrx/pyinstaller-windows 
	cd dist/windows && 7z a skyfwi.7z skyflash-gui/
	cp win-build/7zSD.sfx dist/windows/
	cp win-build/sfx_config.txt dist/windows/
	cd dist/windows && cat 7zSD.sfx sfx_config.txt skyfwi.7z > Skyflash.exe
	mv dist/windows/*.exe final/
	ls -lh final/

win-dev: clean win-flasher-dev ## Create a windows static app using local dev tools (no internet needed if you run "make deps-windows" already)
	docker run --rm -v "$(PWD):/src/" pyinstaller-win64py3:skyflash
	cd dist/windows && 7z a skyfwi.7z skyflash-gui/
	cp win-build/7zSD.sfx dist/windows/
	cp win-build/sfx_config.txt dist/windows/
	cd dist/windows && cat 7zSD.sfx sfx_config.txt skyfwi.7z > Skyflash.exe
	mv dist/windows/*.exe final/
	ls -lh final/

posix-streamer: ## Create the linux/macos streamer to help with the flashing
	cd posix-build && python3 -m PyInstaller -F pypv.py
	chmod +x posix-build/dist/pypv

linux-static: clean posix-streamer ## Create a linux amd64 compatible static (portable) app
	python3 -m PyInstaller skyflash-gui.spec
	cd dist && gzip skyflash-gui
	mv dist/skyflash-gui.gz final/skyflash-gui_linux64-static.gz
	ls -lh final/

macos-app: clean posix-streamer ## Create the macos standalone app
	python3 -m PyInstaller skyflash-gui.spec
	cd dist && tar -cvzf skyflash-app.tgz skyflash-gui.app
	mv dist/skyflash-app.tgz final/skyflash-macos-app.tgz
	ls -lh final/

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
