# HDFury DIVA LED for Home Assistant

Custom Home Assistant integration for controlling the LED strip settings on an
[HDFury DIVA 18Gbps](https://www.hdfury.com/product/4k-diva-18gbps/) over its
HTTP interface.

## Features

- `light` entity for LED on/off, RGB color, and brightness
- configurable static LED color, calibration gains, speeds, delay, gamma, and profiles
- switches for LED enabled, black bar detection, never turn off, and side dimming
- reset button that restores the LED strip to configurable default RGB values
- UI config flow for adding one or more DIVA devices
- UI options flow for changing host/IP and display name later

## Installation

### HACS custom repository

1. In HACS, open **Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add this repository URL:

   ```text
   https://github.com/blbeczech82/hass-hdfury-diva-led
   ```

4. Category: **Integration**.
5. Install **HDFury DIVA LED**.
6. Restart Home Assistant.

### Manual installation

Copy `custom_components/hdfury_diva_led` into your Home Assistant `custom_components`
directory and restart Home Assistant.

## Configuration

In Home Assistant:

1. Go to **Settings -> Devices & services**.
2. Click **Add integration**.
3. Search for **HDFury DIVA LED**.
4. Enter the DIVA host/IP address and name.

To change the host/IP later, open the integration and click **Configure**.

## Entities

The integration creates entities under one DIVA device:

- `light`: LED strip control
- `button`: reset to default color
- `number`: default RGB, static RGB, calibration RGB gain, speed, and global delay
- `select`: active video, syncing, no-signal LED profiles, and video gamma
- `switch`: LED enabled, black bar detect, never turn off, and side dimming

The DIVA does not expose a separate LED brightness value. Brightness is mapped by
scaling the raw RGB channels; the `raw_rgb` attribute shows the values currently
reported by the device.

## Notes

This integration talks to:

- `GET /ssi/brdinfo.ssi` for device identity
- `GET /ssi/toolpage.ssi` for LED state
- `GET /cmd?<key>=<value>` for updates

Tested with HDFury DIVA firmware `0.80.0.14 V3`.
