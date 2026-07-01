# Railroad North - Instructor's Guide (The Brutally Honest Truth)

Here is exactly what you need to know, how the lab works, and what to explain.

## 1. The Brutal Truth: Local vs. AWS

You need to understand the difference between what is running on your laptop right now vs. what will run on AWS later.

**Right Now (Local Laptop - 6 Containers):**
- You are running the **"Slim"** version of the lab. 
- Why? Because your laptop only has 8GB of RAM. The full lab requires 16GB+ RAM. If we ran all 17 containers, your laptop would crash immediately.
- **What is running:** The SCADA Dashboard, the Master PLC, the 3 Slave PLCs, and a basic syslog collector.
- **What you show:** You show the SCADA Dashboard (`http://localhost:8081`). When students do attacks, they will read the logs directly in the terminal (`docker logs railroad-master-plc`) because the heavy Kibana dashboard is NOT running on your laptop.

**Future (AWS - 17 Containers):**
- When you upload this to AWS, you will use `docker-compose-aws.yml`.
- This spins up the extra 11 containers. These containers are the **SOC Stack** (Security Operations Center).
- **What is running:** Elasticsearch, Logstash, Kibana, Zeek IDS, and Network proxies. 
- **What you show:** On AWS, students will have TWO dashboards. The SCADA Dashboard (to control the trains) AND the Kibana Dashboard (to hunt for hackers and read Zeek alerts).

**What to tell your Professor:** 
"Sir, on this laptop, I am demonstrating the core industrial logic (Master-Slave PLCs and SCADA). The heavy SOC monitoring stack (Zeek, ELK, 17 containers total) is configured in a separate deployment file (`docker-compose-aws.yml`) specifically designed to be hosted on our AWS cloud instance, as laptops do not have the RAM to run enterprise-grade SIEMs."

---

## 2. What Do the Students Actually Do?

When a student sits down, they don't just stare at the dashboard. They actively attack it using the terminal.

1. **They read the Slides**: First, you present `railroad-north-presentation.md` so they understand Modbus.
2. **They read the Student Guide**: They open `STUDENT_GUIDE.md` which gives them their step-by-step mission.
3. **They attack the system**: They open a terminal and run the python scripts in the `scripts/` folder (e.g., `python scripts/modbus-attack.py`).
4. **They watch the impact**: They look at the SCADA dashboard to see if they successfully caused a train derailment or bypassed the safety interlock.
5. **They defend**: They look at the terminal logs (or Kibana on AWS) to figure out how to stop the attack.

---

## 3. How to Present This Right Now

**Step 1:** Show the Professor the Marp presentation slides.
**Step 2:** Open `http://localhost:8081` and show the SCADA dashboard. Explain the physical safety interlocks.
**Step 3:** Open a terminal and run `docker stop railroad-slave-plc-1`. Show the professor how the SCADA dashboard immediately turns red and enters a `FAULT` state because the safety heartbeat failed.
**Step 4:** Show the professor the `docker-compose-aws.yml` file to prove that you have the 17-container ELK/Zeek stack ready for the AWS cloud deployment.
