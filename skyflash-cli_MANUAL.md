# Instructions on how to use the skyflash-cli tool

The tool `skyflash-cli` is intended to be run on linux by developers or advancer users and will generate the needed images for the base image.

Once you has created your images you will need to use a tool to burn these images to the uSD cards, we recommend [Balena Etcher](https://www.balena.io/etcher/) a cross OS tool or the venerable `dd` in the console.

## Usage instructions

## Install

To use this tool you need to install skyflash via the .deb file provided in the releases, other kind of installs will not work.

To test if the install was ok, simply run `skyflash-cli` in the console and you will see the usage comments.

### Step 1: Download the default skybian image

Go to [skybian](https://github.com/skycoin/skybian) releases and download the latest image, decompress it and put the base image on a know folder.

### Step 2: Run the tool

`skyflash-cli` has a few options that you can see if you run it without arguments (`skyflash-cli`) or with '-h' switch (`skyflash-cli -h`)

For a default configuration of skybian as a skyminer you just need to run it like this:

```sh
./skyflash-cli -a Skybian-0.1.0.img
```

Where "Skybian-0.1.0.img" is the skybian base image you have downloaded.

This will generate 8 images, one for the manager and 7 minions. Network configuration is the skyminers default:

* Network: 192.168.0.0/24
* Netmask: 255.255.255.0 (aka: /24)
* Gateway: 192.168.0.1
* DNS servers: 1.0.0.1, 1.1.1.1
* Manager IP: 192.168.0.2
* Minions IPs: 192.168.0.[3-9] (7 minions)

If you need a different setup just check the `skyflash-cli -h` to know more, for example for a manager and 22 minions with this details:

* Network: 172.16.22.0/24
* Gateway: 172.16.22.1
* DNS servers: 172.16.22.1, 1.1.1.1
* Manager: 172.16.22.10
* Minions: 172.16.22.100 to 172.16.22.121

**Tip:** If you don't care about the minions IP being contiguous you can declare a range that is greater than the minions count and the script will allocate the IPs in a scattered way inside the range you stated.

```sh
./skyflash-cli -g 172.16.22.1 -d "172.16.22.1, 1.1.1.1" -m 172.16.22.10 -n 100-121 -i Skybian-0.1.0.img
```

Please note that in the case of the DNS (option '-d') if you need to pass more than one IP you need to surround it with double quotes and separate it with a comma and a space, just like the example above.
