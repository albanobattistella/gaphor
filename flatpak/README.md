# Flatpak Packaging for Gaphor

This folder contains some additional files used by Flatpak.

The Flatpak configuration itself is found on
https://github.com/flathub/org.gaphor.Gaphor.

## Create and Install a Flatpak

1. [Install Flatpak](https://flatpak.org/setup)
 
1. Install flatpak-builder
 
       $ sudo apt-get install flatpak-builder

1. Install the GNOME SDK

       $ flatpak install flathub org.gnome.Sdk 3.34

1. Add the Flathub repository and install the necessary SDK:

       $ make setup
	
1. Build Gaphor Flatpak

       $ make
        
1. Install the Flatpak

       $ make install
       
## Update Gaphor Dependencies
In order to update the Gaphor dependencies in the yaml manifest files:

    $ make python-modules 

