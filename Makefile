.DEFAULT_GOAL := help

.PHONY : clean build

PWD = $(shell pwd)
PWDWIN = $(shell pwd)/win-build

clean: ## Clean the environment to have a fresh start
	-sudo rm -rdf skyflash.egg-info
	-sudo rm -rdf deb_dist
	-sudo rm -rdf dist
	-sudo rm -rdf build
	-sudo rm -rdf __pycache__
	-sudo rm -rdf skyflash/__pycache__
	-sudo rm skyflash-*.tar.gz

init: clean ## Initial cleanup, erase even the final app dir
	-rm -rdf final
	-mkdir final
	-cd win-build && sudo rm -rdf dist
	-cd win-build && sudo rm -rdf build
	-cd win-build && sudo rm -rdf __pycache__

build: clean ## Build the pip compatible install file
	python3 setup.py build
	python3 setup.py sdist
	mv dist/skyflash-*.tar.gz final/
	ls -lh final/

install: build ## Install the built pip file
	sudo python3 setup.py install

deb: build ## Create a .deb file ready to use in debian like systems
	sudo python3 setup.py --command-packages=stdeb.command bdist_deb
	cp deb_dist/*all.deb final/
	ls -lh final/

linux-static: clean ## Create a linux amd64 compatible static (portable) app
	python3 -m PyInstaller skyflash-gui.spec
	cd dist && gzip skyflash-gui
	mv dist/skyflash-gui.gz final/skyflash-gui_linux64-static.gz
	ls -lh final/

win-static: clean win-flasher ## Create a windows static (portable) app (needs internet)
	docker run --rm -v "$(PWD):/src/" cdrx/pyinstaller-windows 
	cd dist/windows && 7z a skyfwi.7z skyflash-gui/
	cp win-build/7zSD.sfx dist/windows/
	cp win-build/sfx_config.txt dist/windows/
	cd dist/windows && cat 7zSD.sfx sfx_config.txt skyfwi.7z > Skyflash.exe
	mv dist/windows/*.exe final/
	ls -lh final/

win-flasher: ## Create the flasher tool for windows (needs internet)
	cd win-build && docker run --rm -v "$(PWDWIN):/src/" cdrx/pyinstaller-windows

win-flasher-dev: ## Create the flasher tool for windows (no internet deed if you create the docker machine locally)
	cd win-build && docker run --rm -v "$(PWDWIN):/src/" pyinstaller-win64py3:pyqt

win-dev: clean win-flasher-dev ## Create a windows static app using local dev tools (no internet deed if you create the docker machine locally)
	docker run --rm -v "$(PWD):/src/" pyinstaller-win64py3:pyqt
	cd dist/windows && 7z a skyfwi.7z skyflash-gui/
	cp win-build/7zSD.sfx dist/windows/
	cp win-build/sfx_config.txt dist/windows/
	cd dist/windows && cat 7zSD.sfx sfx_config.txt skyfwi.7z > Skyflash.exe
	mv dist/windows/*.exe final/
	ls -lh final/

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
