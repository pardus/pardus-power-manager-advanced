# Pardus Power Manager
Simple power manager tools written python.

## Features
* performance & powersave profile switch
* automatic profile switch on ac/bat modes
* uses own service

## How to install from source
```shell
# install source
meson setup build --prefix=/usr
ninja -C build install
# enable systemd service (if available)
systemctl enable ppm
# reboot required
reboot
```
## Configuration
Configuration files store in **/etc/pardus/ppm.conf** file and **/etc/pardus/ppm.conf.d/** directory.

## Usage
You can use `ppm` command for changing profile or brightless
```
Usage: ppm [set/get] [mode/backlight] (value)
```
Also you can use indicator from system tray.

## License

Copyright(C) 2021-2024 Ali Rıza KESKİN <ali.riza.keskin@pardus.org.tr>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This package is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

On Debian systems, the complete text of the GNU General
Public License version 3 can be found in "/usr/share/common-licenses/GPL-3".
 
 
