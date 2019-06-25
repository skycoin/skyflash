# Skyflash User's Manual

## Installation & Upgrade

Please refer to the [README](README.md) for install or upgrade instructions.

## Workflow explained

Before looking into it you must know the workflow of the software, Skyflash will do the following tasks for you:

1. Select and verify a Skybian base image, either from a local file or downloading a copy from the internet.
2. Setting your particular network configuration (default Skycoin's Skyminers config is suggested)
3. Build the images for a manager and how many nodes you like (in actual skywire testnet only a manager and 7 nodes are allowed)
4. [Optionally] Burn the images to uSDCards to insert into your Orange Pi Prime SBC.

Now we will explore each option in depth

## Step #1: Select & Verify a Skybian base image

Once you run it for the first time you will be presented with a window like this: (If you are un Windows you will see a extracting dialog first, wait until it finish)

![Start window](/images/start.png)

In this windows you are presented with two choices, download or select a local Skybian base image release file.

### Downloading

A word of caution: if your internet is unstable, limited or slow don't try this option, read the section below; the download process will pull down about 600 MB of data and has no resume option _(blame Github on that)_; if your download get interrupted at 99% it will start over from 0% again!

In the other hand if you have a fast and steady internet connection like more than 4 MBit/sec you are set, select this option and the app will download the image for you, as usual YMMV.

### Selecting a local copy

This is the alternative option if the download option is not the best choice for you because the above mentioned speed/stability issues in your internet link.

Go to a place with a steady and fast internet connection and use whatever device you have (Cell, tablet, laptops, etc) to download the latest Skybian base image. Go to the [Skybian release page](https://github.com/skycoin/skybian/releases/) pick the latest available release (it's the big file ending on .tar.xz) once you get it move it to your PC and click on the "Browse" button to select the file.

### Extract & verify

Either downloading or selecting a local copy, the app will extract the compressed file and then check the integrity of the data inside, all this with feedback of the process for you:

![Extracting the Skybian base image release file](/images/extract.png)
![Verifying the Skybian base image](/images/verify.png)

Yes, it can take a few minutes, it's extracting a ~2GB image from a ~600MB file, and then testing every single bit to get sure you have it right.

### About corrupt files

If the app finds any problem on any of this two operations (mainly due to corrupt files during download) it will let you know with a error/warning dialog box. In any case the solution is to download again the Skybian release file (by the app itself of using an alternative way) and start over.

### About folders and magic

We incorporated a magic effect into Skyflash to ease your life, go & close the app at this point and re-open it... you will see it knows that it has already a Skybian base image and it will show ready for steps #2 & #3

The magic resides in the Skyflash app folder, once you run it for the first time it will create a folder named Skyflash in a specific place depending on your OS:

| Operating System | Path |
|:---:|:---:|
| Windows | My Documents\Skyflash |
| Linux | ~/Skyflash |
| MacOS | ~/Skyflash |

Please take a moment to find this folder, inside it you will find at least a `Downloads` folder and a file called Skyflash.log

The download folder is the place where the app put the downloaded & extracted base images plus some other files, the Skyflash.log file is just that: the log file for all operations & you will love it if you get in trouble at some point.

This folder will also be the default place for your custom Skybian images _(you can change this later)_, so don't forget it.

## Step #2: Network configuration

Once you reach this point the app's window looks like this:

![Network configuration defaults](/images/net-default.png)

If you plan to run a Skyminer with the default network configuration for the testnet you are set, you can jump to step #3 (if you are curious about the default network config, just un-tick the `Use Skyminer's defaults` box to see it on details, but remember to tick it again)

If you plan to run it on an already existent network and you need to tweak the network parameters then un-tick the `Use Skyminer's defaults` box to see and edit the network details. If you do that it will show it like this:

![Editing network configuration](/images/net-edit.png)

The app has some logic rules you need to obey when modifying the network settings:

* We use a `/24` network segment _(255.255.255.0 netmask if you prefer it on this format)_
* Because of that the `Manager IP` address must need to be in the same network segment of the `Gateway`.
* We use CloudFlare/OpenDNS DNS servers instead of Google ones, if you want to use a local one put it first and keep a CloudFlare/OpenDNS DNS servers in second place, you can put up to three nameserver IPs
* The node count refers to the nodes only (7 nodes + one manager), we assume you want to always config a managers node; because of this you can also specify a count of 0 nodes and the app will only create a manager node image with no nodes _(useful for a quick test of the overall work flow, and for developing purposes)_

If you manage to break some of this rules (and other trivial ones) the app will complain suggesting where the trouble is.

## Step #3: Image generation

Once you has the network config in place it's time to generate your custom Skybian images, once you click on the `Build the images` button, you will be presented with a popup like this:

![Default build path](/images/build_path_ask.png)

Here you can click `Yes` to use the mentioned path or decline (`No`) to pick another one, the `No` option will present you a standard folder pick dialog for you to select a new path.

A word here if you are using a laptops/PC with a SSD: usually the SSD drives are small and free space always tend to zero, if you don't has about 20 GB of free space in your system partition you may need to pick the `No` option and select another location

This is useful also when you have more than one Skyminer with different configs: you can keep two or more sets of images in different folders 

After completing this step just hit the `Build Images` button and go for a soft drink/beer/coffee as this can take a while.

The process of generate the images is a HDD intensive task and depending on you PC it can take from 3 to more than 5 minutes to generate the 8 images on actual hardware. In this period your PC may looks like irresponsible at times, be patient and wait until it finish.

During the image generation you may see a windows like this to show you the process:

![Building images](/images/images.png)

When this process finish you will have the images in your selected Skybian folder, they will have names like `Skybian-manager.img` & `Skybian-node-1.img` and so on.

## Step #4: Flashing the images

![Ready to flash the images](/images/flashing-start.png)

You may want to flash the image now or later, if you want to do it now then you may follow the steps below, if not we recommend [BalenaEtcher](https://www.balena.io/etcher/) a multi-platform flashing tool that will do the task once you have the images generated.

**A word of warning:** once you generate the images and close Skyflash you will not be able to use Skyflash to burn the same images unless you re-generate the images. For this reason we recommend to have a copy of BalenaEtcher at hand to burn the previously generated images.

To start the flashing process you need to select the proper device, and image in the combo boxes, but first a needed warning:

### WARNING!

The flashing process **is not reversible**, please double check that the device selected on the combo box is the correct one or you may flash the Skybian Image to one of your USB Flash drives, rendering it unusable and will loss the data on it

The process to detect the correct uSDCard device is tricky and we have to extend it to a few common devices, that may lead into false detection of flash thumb drives.

**We recommend to only have the card inserted at this step, please disconnect any other USB storage device before picking the correct device; at the end double and triple check that the device selected is the real SD card on the slot**

After this you can click on the `Start flashing` button, a sample flashing in progress looks like this:

![Flashing the images](/images/flashing-in-progress.png)

Once the flashing of that device ends a popup dialog will explain that you can now remove the SD card from the PC and insert another one to continue the flashing, wait a few moments for the card to be detected, select the next image from the drop down menu and hit the `Start flashing` button again; repeat this until you end flashing all the images

### SD Cards and flash process duration

The flash process depends on the speed of your SD card, using Class 10 or higher class cards is mandatory or you will risk your data with an failed card due to wear out or experience low performance.

But yes, flashing one card can take about 3 to 5 minutes depending on flash class & specs.

## Why skyflash ask for credentials or privileged operations?

Flashing to a uSD Card is a privileged operation and Skyflash has built a mechanism to get that privileges at some point.

Depending on your operating system you will see a credential asking box sooner or later, in Windows the privilege asking happens at the start of the app, on Linux on the start of each flash operation.
