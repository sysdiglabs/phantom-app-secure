# Phantom Application for Sysdig Secure

This application integrates Phantom with [Sysdig Secure](https://sysdig.com/products/secure/) and allows you 
to create [capture files](https://sysdigdocs.atlassian.net/wiki/spaces/Monitor/pages/205684760/Captures) that can be
analyzed with [Sysdig Inspect](https://sysdig.com/opensource/inspect/) for further troubleshooting.

## Build 

If you want to build the application for a future installation into Phantom, execute:

```sh
$ make
```

This will create a file called `sysdig.tar.gz`.

## Install

Go to `Apps > Install App` and drag & drop the file `sysdig.tar.gz` into this box. Click on Install and it will be installed.

## Configure

Once you instsall it, you need to configure it. Look for `Unconfigured Apps` and click on `Configure New Asset`.

Give it a name and in the Asset Settings fill your Kubeconfig encoded in Base64, for example: 

```sh
$ cat kubeconfig | base64 -w 0; echo
```

Copy and paste the content into the input.

Set the number of seconds which Sysdig has to be capturing data, and fill the [API token](https://secure.sysdig.com/#/settings/user) from Sysdig Secure.


