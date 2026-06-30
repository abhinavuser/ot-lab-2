# Railroad North - OT Security Training Lab

This repository contains a full Operational Technology (OT) and ICS security training lab. It simulates a railway control system using a Master/Slave PLC architecture, allowing students to learn about Modbus TCP, physical safety interlocks, and how to defend against cyber-physical attacks.

## How to Run the Lab

You will need Docker and Docker Compose installed to run this environment. 

We provide two deployment options depending on your hardware:

1. **Local Testing (Slim Setup)**: Uses lightweight containers so it won't crash standard laptops (requires <8GB RAM). 
   ```bash
   docker-compose up -d
   ```

2. **AWS / Cloud Deployment (Full SOC Setup)**: Includes the heavy ELK stack (Elasticsearch, Logstash, Kibana) and Zeek IDS. Use this if you are running on a server with 16GB+ RAM.
   ```bash
   docker-compose -f docker-compose-aws.yml up -d
   ```

To stop the lab and clean up the containers, run:
```bash
docker-compose down
```

## Accessing the Lab

Once the containers are running, you can access the main components:

- **SCADA Dashboard**: [http://localhost:8081](http://localhost:8081) (The main operator interface)
- **Master PLC Logs**: Run `docker logs -f railroad-master-plc` to watch the Modbus traffic and safety logic in real time.

## Architecture

The lab strictly follows the Purdue Enterprise Reference Architecture across three segmented networks:
- **IT Network**: Engineering workstations and file transfers.
- **DMZ Network**: Hosts the SCADA Web Dashboard.
- **OT Network**: Hosts the Master PLC (coordinator) and 3 Slave PLCs (North, Central, South) communicating over unencrypted Modbus TCP.

## Training Presentation

A detailed presentation designed for students is included in the `training-materials/` directory. 
- File: `training-materials/railroad-north-presentation.md`
- You can view and export these slides using the "Marp for VS Code" extension. It covers the IT vs. OT differences, Modbus vulnerabilities, and walks through the 4 attack scenarios.
