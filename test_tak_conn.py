
import asyncio
import pytak
from configparser import ConfigParser
import os

TAK_SERVER = "165.1.73.192"
TAK_PORT = 8089
TAK_USER_P12 = "/home/phill/esp/atfsphilliez/ATAK/cert/philliez.p12"
TAK_CA_CRT = "/home/phill/esp/atfsphilliez/ATAK/cert/ca.crt"
TAK_PASSWORD = "FWb9KSwAemRzwgcgFEChY5oWkwivlPT9"

async def test_conn():
    config_dict = {
        "COT_URL": f"ssl://{TAK_SERVER}:{TAK_PORT}",
        "PYTAK_TLS_CLIENT_CERT": TAK_USER_P12,
        "PYTAK_TLS_CLIENT_PASSWORD": TAK_PASSWORD,
        "PYTAK_TLS_CLIENT_CAFILE": TAK_CA_CRT,
        "PYTAK_TLS_DONT_CHECK_HOSTNAME": "1",
    }
    
    config_p = ConfigParser()
    config_p.add_section("test")
    config = config_p["test"]
    for k, v in config_dict.items():
        config[k] = v

    print(f"[*] Testing connection to {config['COT_URL']}...")
    try:
        # This will try to open the connection
        reader, writer = await pytak.protocol_factory(config)
        print("[+] Connection successful!")
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"[-] Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())
