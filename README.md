# skyflash a tool to configure & flash skybian base images for the skycoin skyminers

With this tool you will be able configure the default [skybian](https://github.com/simelo/skybian) image to your custom environment and create the needed images for it.

The resulting images will only run on the official skyminer hardware, aka: Orange Pi Prime SBC.

The tool has two variants:

* A Linux CLI tool (skyflash-cli) **_for developers and advanced users_**.
* A Linux/Mac/Windows GUI tool (skyflash.py) for all users written in python.

## skyflash-cli tool

The tool `skyflash-cli` is intended to be run on linux (soon on Mac too) and will generate the needed images for a base image.

Then you need to use a tool to burn these images to the uSD cards, we recommend BalenaEtcher a cross OS tool.

### Step 1: Download the default skybian image

Go to [skybian](https://github.com/simelo/skybian) releases and download the latest image, decompress it and put the base image on the folder where `skyflash-cli` resides; or copy the `skyflash-cli` tool to the folder where you have the skybian image.

### Step 2: Run the tool

`skyflash-cli` has a few options that you can see if you run it without arguments (`skyflash-cli`) or with '-h' switch (`skyflash-cli -h`)

For a default configuration of skybian as a skyminer you just need to run it like this:

```
./skyflash-cli -a Skybian-0.1.0.img
```

This will generate 8 images, one for the manager and 7 nodes. Network configuration is the skyminers default:

* Network: 192.168.0.0/24
* Netmask: 255.255.255.0 (aka: /24)
* Gateway: 192.168.0.1
* DNS servers: 1.0.0.1, 1.1.1.1
* Manager IP: 192.168.0.2
* Node IPs: 192.168.0.[3-9] (7 nodes)

If you need a different setup just check the `skyflash-cli -h` to know more, for example for a manager and 22 nodes with this details:

* Network: 172.16.22.0/24
* Gateway: 172.16.22.1
* DNS servers: 172.16.22.1, 1.1.1.1
* Manager: 172.16.22.10
* Nodes: 172.16.22.100 to 172.16.22.121

**Tip:** If you don't care about the nodes IP being contiguous you can declare a range that is greater than the node count and the script will allocate the IPs in a scattered way inside the range you stated.

```
./skyflash-cli -g 172.16.22.1 -d "172.16.22.1, 1.1.1.1" -m 172.16.22.10 -n 100-121 -i Skybian-0.1.0.img
```

Please note that in the case of the DNS (option '-d') if you need to pass more than one IP you need to surround it with double quotes and separate it with a comma and a space, just like the example above.

## skyflash.py tool

This is a work in progress by now, check back later or go to the develop branch to test the lastest features.
