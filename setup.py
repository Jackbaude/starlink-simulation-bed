# SPDX-License-Identifier: GPL-2.0-only
#
# Ported to Python by Mohit P. Tahiliani
#

try:
    from ns import ns
except ModuleNotFoundError:
    raise SystemExit(
        "Error: ns3 Python module not found;"
        " Python bindings may not be enabled"
        " or your PYTHONPATH might not be properly configured"
    )
import sys
from ctypes import c_bool, c_int


def TxCallback(packet):
    tx_time = ns.core.Simulator.Now().GetSeconds()
    print(f"Packet transmitted at {tx_time} seconds. Packet size: {packet.GetSize()} bytes")

def RxCallback(packet, address):
    rx_time = ns.core.Simulator.Now().GetSeconds()
    print(f"Packet received at {rx_time} seconds from {address}. Packet size: {packet.GetSize()} bytes")

error_model = ns.CreateObject[ns.RateErrorModel]()
error_model.SetAttribute("ErrorRate", ns.DoubleValue(0.00))  # 1% packet loss

nCsma = c_int(3)
verbose = c_bool(True)
cmd = ns.CommandLine(__file__)
cmd.AddValue("nCsma", "Number of extra CSMA nodes/devices", nCsma)
# cmd.AddValue("verbose", "Tell echo applications to log if true", verbose)
cmd.Parse(sys.argv)

if verbose.value:
    ns.LogComponentEnable("UdpEchoClientApplication", ns.LOG_LEVEL_INFO)
    ns.LogComponentEnable("UdpEchoServerApplication", ns.LOG_LEVEL_INFO)

# Create 4 nodes
nodes = ns.NodeContainer()
nodes.Create(4)  # Create 4 nodes

# Create PointToPointHelper and configure links between nodes
pointToPoint = ns.PointToPointHelper()
pointToPoint.SetDeviceAttribute("DataRate", ns.StringValue("5Mbps"))
pointToPoint.SetChannelAttribute("Delay", ns.StringValue("2ms"))

# Install point-to-point links between N1-N2, N2-N3, N3-N4
devices12 = pointToPoint.Install(nodes.Get(0), nodes.Get(1))
devices23 = pointToPoint.Install(nodes.Get(1), nodes.Get(2))
devices34 = pointToPoint.Install(nodes.Get(2), nodes.Get(3))

devices12.Get(1).SetReceiveErrorModel(error_model) 
devices23.Get(1).SetReceiveErrorModel(error_model) 
devices34.Get(1).SetReceiveErrorModel(error_model) 

# Add Internet stack
stack = ns.InternetStackHelper()
stack.Install(nodes)

# Assign IP addresses to the links
address = ns.Ipv4AddressHelper()

# N1-N2
address.SetBase(ns.Ipv4Address("10.1.1.0"), ns.Ipv4Mask("255.255.255.0"))
interfaces12 = address.Assign(devices12)

# N2-N3
address.SetBase(ns.Ipv4Address("10.1.2.0"), ns.Ipv4Mask("255.255.255.0"))
interfaces23 = address.Assign(devices23)

# N3-N4
address.SetBase(ns.Ipv4Address("10.1.3.0"), ns.Ipv4Mask("255.255.255.0"))
interfaces34 = address.Assign(devices34)

# Populate routing tables
ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

# Configure echo server on N4
echoServer = ns.UdpEchoServerHelper(9)
serverApps = echoServer.Install(nodes.Get(3))  # N4 as server
serverApps.Start(ns.Seconds(1.0))
serverApps.Stop(ns.Seconds(10.0))

# Configure echo clients for bidirectional communication

# Client on N1 to send packets to N2
echoClientN1 = ns.UdpEchoClientHelper(interfaces12.GetAddress(1).ConvertTo(), 9)
echoClientN1.SetAttribute("MaxPackets", ns.UintegerValue(10))  # Increase the number of packets
echoClientN1.SetAttribute("Interval", ns.TimeValue(ns.Seconds(1.0)))
echoClientN1.SetAttribute("PacketSize", ns.UintegerValue(1024))

clientAppsN1 = echoClientN1.Install(nodes.Get(0))  # N1 as client
clientAppsN1.Start(ns.Seconds(2.0))
clientAppsN1.Stop(ns.Seconds(10.0))

# Client on N2 to send packets to N1
echoClientN2 = ns.UdpEchoClientHelper(interfaces12.GetAddress(0).ConvertTo(), 9)
echoClientN2.SetAttribute("MaxPackets", ns.UintegerValue(10))  # Increase the number of packets
echoClientN2.SetAttribute("Interval", ns.TimeValue(ns.Seconds(1.0)))
echoClientN2.SetAttribute("PacketSize", ns.UintegerValue(1024))

clientAppsN2 = echoClientN2.Install(nodes.Get(1))  # N2 as client
clientAppsN2.Start(ns.Seconds(3.0))
clientAppsN2.Stop(ns.Seconds(10.0))

# Client on N2 to send packets to N3
echoClientN2N3 = ns.UdpEchoClientHelper(interfaces23.GetAddress(1).ConvertTo(), 9)
echoClientN2N3.SetAttribute("MaxPackets", ns.UintegerValue(10))  # Increase the number of packets
echoClientN2N3.SetAttribute("Interval", ns.TimeValue(ns.Seconds(1.0)))
echoClientN2N3.SetAttribute("PacketSize", ns.UintegerValue(1024))

clientAppsN2N3 = echoClientN2N3.Install(nodes.Get(1))  # N2 as client to N3
clientAppsN2N3.Start(ns.Seconds(4.0))
clientAppsN2N3.Stop(ns.Seconds(10.0))

# Client on N3 to send packets to N2
echoClientN3 = ns.UdpEchoClientHelper(interfaces23.GetAddress(0).ConvertTo(), 9)
echoClientN3.SetAttribute("MaxPackets", ns.UintegerValue(10))  # Increase the number of packets
echoClientN3.SetAttribute("Interval", ns.TimeValue(ns.Seconds(1.0)))
echoClientN3.SetAttribute("PacketSize", ns.UintegerValue(1024))

clientAppsN3 = echoClientN3.Install(nodes.Get(2))  # N3 as client
clientAppsN3.Start(ns.Seconds(5.0))
clientAppsN3.Stop(ns.Seconds(10.0))

# Client on N3 to send packets to N4
echoClientN3N4 = ns.UdpEchoClientHelper(interfaces34.GetAddress(1).ConvertTo(), 9)
echoClientN3N4.SetAttribute("MaxPackets", ns.UintegerValue(10))  # Increase the number of packets
echoClientN3N4.SetAttribute("Interval", ns.TimeValue(ns.Seconds(1.0)))
echoClientN3N4.SetAttribute("PacketSize", ns.UintegerValue(1024))

clientAppsN3N4 = echoClientN3N4.Install(nodes.Get(2))  # N3 as client to N4
clientAppsN3N4.Start(ns.Seconds(6.0))
clientAppsN3N4.Stop(ns.Seconds(10.0))

# Client on N4 to send packets to N3
echoClientN4 = ns.UdpEchoClientHelper(interfaces34.GetAddress(0).ConvertTo(), 9)
echoClientN4.SetAttribute("MaxPackets", ns.UintegerValue(10))  # Increase the number of packets
echoClientN4.SetAttribute("Interval", ns.TimeValue(ns.Seconds(1.0)))
echoClientN4.SetAttribute("PacketSize", ns.UintegerValue(1024))

clientAppsN4 = echoClientN4.Install(nodes.Get(3))  # N4 as client
clientAppsN4.Start(ns.Seconds(7.0))
clientAppsN4.Stop(ns.Seconds(10.0))

# Enable packet capture for each link
pointToPoint.EnablePcap("pcap/N1-N2", devices12.Get(0), True)
pointToPoint.EnablePcap("pcap/N2-N3", devices23.Get(0), True)
pointToPoint.EnablePcap("pcap/N3-N4", devices34.Get(0), True)


# Print interface addresses
print("N1-N2 Interface:", interfaces12.GetAddress(0), "-", interfaces12.GetAddress(1))
print("N2-N3 Interface:", interfaces23.GetAddress(0), "-", interfaces23.GetAddress(1))
print("N3-N4 Interface:", interfaces34.GetAddress(0), "-", interfaces34.GetAddress(1))

print("Assigned IP addresses:")
print(f"N1 IP: {interfaces12.GetAddress(0)}")
print(f"N2 IP: {interfaces12.GetAddress(1)}")
print(f"N2 IP: {interfaces23.GetAddress(0)}")
print(f"N3 IP: {interfaces23.GetAddress(1)}")
print(f"N3 IP: {interfaces34.GetAddress(0)}")
print(f"N4 IP: {interfaces34.GetAddress(1)}")


# devices12.Get(0).TraceConnectWithoutContext("PhyTxBegin", TxCallback)
# devices12.Get(1).TraceConnectWithoutContext("PhyRxEnd", RxCallback)

# Run the simulation
ns.Simulator.Run()
ns.Simulator.Destroy()


