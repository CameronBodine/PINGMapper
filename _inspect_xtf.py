import pyxtf
from pathlib import Path

path = Path("C:\\Users\\cbodine\\Downloads\\sonar_data141023195000.xtf")
header, packets = pyxtf.xtf_read(str(path))
sonar_packets = packets.get(pyxtf.XTFHeaderType.sonar, [])
print("sonar packets:", len(sonar_packets))
if sonar_packets:
    ping = sonar_packets[0]
    print("ping type:", type(ping))
    print("ping attrs:", [a for a in dir(ping) if not a.startswith("_")])
    if hasattr(ping, "ping_chan_headers") and ping.ping_chan_headers:
        ch = ping.ping_chan_headers[0]
        print("chan header type:", type(ch))
        print("chan header attrs:", [a for a in dir(ch) if not a.startswith("_")])
