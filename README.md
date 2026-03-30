# WiFi-DensePose to TAK Bridge

This project acts as a bridge between the WiFi-DensePose sensing server and a TAK (Team Awareness Kit) server. It polls detections from the sensing server and forwards them as Cursor-on-Target (CoT) events to the TAK server.

## Features
- Real-time polling of WiFi-DensePose sensing results.
- Automatic CoT event generation for presence detection and vital signs.
- Secure SSL connection to TAK servers using certificate-based authentication.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/philliez/wifi-densepose-tak-bridge.git
    cd wifi-densepose-tak-bridge
    ```
2.  Install dependencies:
    ```bash
    pip install pytak requests
    ```

## Usage

1.  Ensure you have your TAK certificates (`.p12` and `ca.crt`) in a secure location.
2.  Run the bridge:
    ```bash
    python tak_bridge.py \
      --tak-server 165.1.73.192 \
      --tak-port 8089 \
      --p12 /path/to/your/cert.p12 \
      --ca /path/to/your/ca.crt \
      --password YOUR_CERT_PASSWORD \
      --sensing-server http://localhost:8080 \
      --callsign WiFi-DP-Sensor-1
    ```

## TAK Server Integration

This bridge is designed to connect to TAK servers (like FTS or WinTAK/ATAK) via SSL.
- **Port:** 8089 (Standard SSL port)
- **Authentication:** P12 Certificate
- **Data Format:** CoT (Cursor-on-Target)

## License
MIT
