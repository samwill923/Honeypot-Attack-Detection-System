# Honeypot Attack Detection System

A lightweight cyber-security honeypot that simulates fake network services, captures incoming connection attempts, and visualizes them in real time through a React dashboard.  
This project demonstrates attacker behavior analysis, network monitoring, and intrusion detection concepts.


##  Project Structure

```
cyber-project/
│
├── backend_real.py          # Flask API + honeypot listeners
├── attempts.csv             # Auto-generated attack log file
│
├── frontend/                # React dashboard
│   ├── package.json
│   ├── package-lock.json
│   ├── public/
│   └── src/
│
├── README.md
└── .gitignore
```


##  Features

- Fake SSH, HTTP, and custom services on **ports 2222, 8080, 50022**
- Logs:
  - attacker IP  
  - attacker source port  
  - target port  
  - payload preview  
  - timestamp  
  - banner sent back  
- Real-time monitoring dashboard (React)
- Live activity section
- Quick statistics (top ports, top IPs, total attempts)
- Time-series chart of attack bursts
- Downloadable CSV log file
- Simulation buttons for demo purposes


##  Backend Setup (Python + Flask)

### Requirements  
- Python 3.8+
- flask  
- flask-cors  

### Installation  
```bash
pip install flask flask-cors
```

### Run Backend  
```bash
cd cyber-project
python backend_real.py
```

The backend will start the honeypot listeners and expose the API at:
```
http://localhost:5000
```


##  Frontend Setup (React)

### Requirements  
- Node.js  
- npm  

### Installation  
```bash
cd frontend
npm install
```

### Run Frontend  
```bash
npm start
```

Then open:
```
http://localhost:3000
```


##  How the System Works

- The backend opens **fake network ports** and pretends to be real services.
- Any device that touches these ports is logged as a potential scan or intrusion attempt.
- Logged data is sent to the frontend through the Flask API.
- The dashboard visualizes:
  - Live activity
  - Attack logs
  - Most targeted ports
  - Behaviour patterns over time
- Clicking “Download CSV” exports all captured attack attempts.


##  Screenshots
<img width="1876" height="863" alt="image" src="https://github.com/user-attachments/assets/9a9cefbe-f3ce-492a-abc9-165de094feb4" />

<img width="1795" height="775" alt="image" src="https://github.com/user-attachments/assets/f073e965-3aee-4307-8dd6-3e5e18211cb7" />

##  License

Permission to be taken before use


##  Credits

- Backend: Python Flask + Socket servers  
- Frontend: React.js  
- Design & architecture: Honeypot-based intrusion detection  
