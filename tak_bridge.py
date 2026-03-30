
import asyncio
import argparse
import requests
import xml.etree.ElementTree as ET
from configparser import ConfigParser
import pytak

# Default configuration
DEFAULT_TAK_SERVER = "165.1.73.192"
DEFAULT_TAK_PORT = "8089"
DEFAULT_P12_PATH = "/home/phill/esp/atfsphilliez/ATAK/cert/philliez.p12"
DEFAULT_CA_PATH = "/home/phill/esp/atfsphilliez/ATAK/cert/ca.crt"
DEFAULT_PASSWORD = "FWb9KSwAemRzwgcgFEChY5oWkwivlPT9"
DEFAULT_SENSING_SERVER = "http://localhost:8080"
DEFAULT_CALLSIGN = "WiFi-DP-Sensor-1"
DEFAULT_LAT = 50.8225
DEFAULT_LON = -0.1375

class DensePoseWorker(pytak.QueueWorker):
    """
    Worker that polls the WiFi-DensePose sensing server and puts CoT events on the queue.
    """
    def __init__(self, queue, config, sensing_server, callsign, lat, lon):
        super().__init__(queue, config)
        self.sensing_server = sensing_server
        self.callsign = callsign
        self.lat = lat
        self.lon = lon

    async def handle_data(self, data):
        # This worker only produces data, it doesn't handle incoming data from its own queue
        pass

    async def run(self, _=-1):
        self._logger.info(f"Starting DensePose polling loop for {self.sensing_server}...")
        last_state = None
        
        while True:
            try:
                # Poll the latest sensing update (using asyncio.to_thread for the synchronous requests call)
                resp = await asyncio.to_thread(
                    requests.get, 
                    f"{self.sensing_server}/api/v1/sensing/latest", 
                    timeout=2
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    # Check for presence in classification
                    presence = data.get('classification', {}).get('presence', False)
                    vitals = data.get('vital_signs')
                    
                    # Send update if presence detected OR if state changed (to send a "clear" event)
                    if presence or last_state != presence:
                        event = self.create_cot(presence, vitals)
                        await self.put_queue(event)
                        state_str = "DETECTED" if presence else "CLEAR"
                        self._logger.info(f"Presence: {state_str} -> CoT Queued")
                        last_state = presence
                else:
                    self._logger.warning(f"Sensing server returned status {resp.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self._logger.error(f"Error polling sensing server: {e}")
            except Exception as e:
                self._logger.exception(f"Unexpected error in polling loop: {e}")
                
            await asyncio.sleep(2)  # Poll every 2 seconds

    def create_cot(self, presence, vitals):
        """Creates a Cursor on Target (CoT) XML event."""
        status = "detected" if presence else "clear"
        remarks = f"WiFi DensePose Detection: {status}"
        
        if vitals and presence:
            hr = vitals.get('heart_rate_bpm', 'N/A')
            br = vitals.get('breathing_rate_bpm', 'N/A')
            remarks += f" | HR: {hr} BPM | BR: {br} BPM"
        
        # Generate base CoT XML using pytak helper
        # a-u-G = Atom-Unmanned-Ground (Generic sensor)
        event = pytak.gen_cot_xml(
            uid=f"WiFiDP-{self.callsign}",
            callsign=self.callsign,
            lat=str(self.lat),
            lon=str(self.lon),
            cot_type="a-u-G"
        )
        
        # Add custom detail elements
        detail = event.find("detail")
        
        # Status element
        status_el = ET.SubElement(detail, "status")
        status_el.set("status", status)
        
        # Remarks
        remarks_el = ET.SubElement(detail, "remarks")
        remarks_el.text = remarks
        
        # If we have vitals, add them as track info or similar if desired
        # For now, they are in the remarks
        
        return ET.tostring(event)

async def main():
    parser = argparse.ArgumentParser(description="WiFi-DensePose to TAK Bridge")
    parser.add_argument("--tak-server", default=DEFAULT_TAK_SERVER, help="TAK Server IP")
    parser.add_argument("--tak-port", default=DEFAULT_TAK_PORT, help="TAK Server Port (usually 8089 for SSL)")
    parser.add_argument("--p12", default=DEFAULT_P12_PATH, help="Path to .p12 certificate")
    parser.add_argument("--ca", default=DEFAULT_CA_PATH, help="Path to CA certificate")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Certificate password")
    parser.add_argument("--sensing-server", default=DEFAULT_SENSING_SERVER, help="WiFi-DensePose Server URL")
    parser.add_argument("--callsign", default=DEFAULT_CALLSIGN, help="TAK Callsign")
    parser.add_argument("--lat", type=float, default=DEFAULT_LAT, help="Sensor Latitude")
    parser.add_argument("--lon", type=float, default=DEFAULT_LON, help="Sensor Longitude")
    parser.add_argument("--no-verify", action="store_true", help="Disable SSL certificate verification")
    args = parser.parse_args()

    # Build PyTAK configuration
    config_dict = {
        "COT_URL": f"ssl://{args.tak_server}:{args.tak_port}",
        "PYTAK_TLS_CLIENT_CERT": args.p12,
        "PYTAK_TLS_CLIENT_PASSWORD": args.password,
        "PYTAK_TLS_CLIENT_CAFILE": args.ca,
        "PYTAK_TLS_DONT_CHECK_HOSTNAME": "1",
    }
    
    if args.no_verify:
        config_dict["PYTAK_TLS_DONT_VERIFY"] = "1"

    # PyTAK expects a ConfigParser/SectionProxy
    config_p = ConfigParser()
    config_p.add_section("bridge")
    config = config_p["bridge"]
    for k, v in config_dict.items():
        config[k] = v

    # Initialize PyTAK CLI Tool
    clitool = pytak.CLITool(config)
    
    # Set up standard TAK workers (TX and RX)
    await clitool.setup()
    
    # Add our custom DensePose worker
    dp_worker = DensePoseWorker(
        clitool.tx_queue, 
        config, 
        args.sensing_server, 
        args.callsign, 
        args.lat, 
        args.lon
    )
    clitool.add_task(dp_worker)
    
    print(f"[*] TAK Bridge Started.")
    print(f"[*] Forwarding to {config['COT_URL']}")
    print(f"[*] Monitoring Sensing Server: {args.sensing_server}")
    
    # Run the tool and all its tasks
    await clitool.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
