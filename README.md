# Cuttyhunk_Wx_St_Live
Live code of Cuttyhunk_Wx_St

Sensors: Arduino Pro Mini (Mega328, v3.3, 8mHz with BME280 sensor, transmitting via HopeRF RMF95x (915mHz), powered by x2 AA)
Gateway: Adafruit Feather 32u4 (datalogger) recieving via HopeRF RFM95x (915 mHz) and passing data to RPi3 via serial port
Processing: RPi3, python script logging/pushing data to ThingSpeak/Twitter/Local Logs, updating SVG to be displayed on a jailbroken Kindle2i.

Future Research: 

https://voyager.lupomesky.cz/howto/raspi-4g-ap/ (RPi as 4G(LTE) Hotspot/Gateway/AP
https://sigquit.wordpress.com/2012/08/20/an-introduction-to-libqmi/ 


Dynamic DNS provided by http://freedns.afraid.org/
