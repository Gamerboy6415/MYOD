## MYOD (Make Your Own Dasdec)
## !!!
## !!! THIS IS FOR PEOPLE VIEWING... THIS IS FOR NOLAN TV.. THIS IS SOMETHING THAT I'M EDITING FOR MY NOLANTV... PELASE IGNORE THIS...
## !!! ALL UPDATES FOR THIS HAVE BEEN CANCELLED TO BE REPLACED BY NOLANTV SETTINGS
## !!!
What you need:
- A fresh installation of Ubuntu Server. i used 24.04.3 and thats what this guide is written for, but you can probably get away with other versions
- Internet connection on the target machine/vm

# Installation

1. Install Ubuntu Server. You MUST make sure the username is "main". If you use a different username you must modify the scripts to use it.

2. Login and clone this repository
```bash
git clone https://github.com/Gamerboy6415/MYOD.git
cd MYOD
```
3. Make the install script executable and run it
```bash
chmod +x install.sh
./install.sh
```
Do not run the script with sudo, it will fail if you do. Deleting the QuantumENDEC and dasdec folders in the home directory and recloning will allow you to rerun the script.

4. Reboot the machine
```bash
sudo reboot
```

After the system reboots, it should automatically display the alert renderer.

* Make sure the system is connected to the internet. Press the "i" key to display the IP address of the machine.
* You can access the control panel by navigating to `http://<IP_ADDRESS>:8050` in your web browser. QuantumENDEC can be accessed at `http://<IP_ADDRESS>:5000`. Default password is 'hackme', you should change it immediately.
The control panel is mostly unfinished right now
* **Make sure to enable audio output and input within QuantumENDEC settings, they should be set to the 'pulse' setting.**

# License
This project is licensed under the GNU General Public License v3.0 License - see the [LICENSE](LICENSE.md) file for details
This project contains a modified version of the original [QDEC by ApatheticDELL](https://github.com/ApatheticDELL/QDEC)
