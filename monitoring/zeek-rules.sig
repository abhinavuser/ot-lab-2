# Zeek signature file for Railroad North

# Detect unauthorized Modbus TCP traffic
signature modbus-unauthorized-access {
  ip-proto == tcp
  dst-port == 502
  src-ip !in [172.25.0.0/16, 172.27.0.0/16]
  event "Unauthorized Modbus Access Attempt"
}

# Detect high-frequency Modbus reads (port scanning)
signature modbus-reconnaissance {
  ip-proto == tcp
  dst-port == 502
  tcp-state == syn
  event "Potential Modbus Reconnaissance"
}

# Detect anomalous Modbus payload sizes
signature modbus-payload-anomaly {
  ip-proto == tcp
  dst-port == 502
  payload-size > 256
  event "Unusually Large Modbus Payload"
}

# Detect syslog tampering attempts
signature syslog-injection-attempt {
  ip-proto == udp
  dst-port == 514
  payload /.*; .*|.*`|.*\$\(.*\)/
  event "Potential Syslog Injection"
}

# Detect traffic to/from PLC from unauthorized sources
signature plc-unauthorized-source {
  ip-proto == tcp
  dst-ip in [172.25.1.10, 172.25.2.10, 172.25.3.10]
  src-ip !in [172.25.0.0/16, 172.27.0.0/16]
  event "Unauthorized Source to Slave PLC"
}
