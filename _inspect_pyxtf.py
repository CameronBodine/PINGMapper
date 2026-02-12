import pyxtf

print("pyxtf module:", pyxtf)
print("pyxtf attrs:", [a for a in dir(pyxtf) if a.startswith("XTF")])
for name in ["XTFPacketHeader", "XTFPacketHeaderType", "XTFHeaderType", "XTFPingHeader"]:
    if hasattr(pyxtf, name):
        obj = getattr(pyxtf, name)
        print(name, obj)
