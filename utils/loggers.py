# utils/loggers.py
import csv
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class CSVLogger:
    """Simple CSV-based logging"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
    
    def log_spi_packet(self, packet_data: Dict):
        """Log SPI packet transmission"""
        filename = self.log_dir / f"spi_packets_{datetime.now().strftime('%Y%m%d')}.csv"
        file_exists = filename.exists()
        
        with open(filename, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=packet_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(packet_data)
    
    def log_motor_state(self, grid_state: List[Dict]):
        """Log motor grid state"""
        filename = self.log_dir / f"motor_states_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='') as f:
            if grid_state:
                writer = csv.DictWriter(f, fieldnames=grid_state[0].keys())
                writer.writeheader()
                writer.writerows(grid_state)

class DatabaseLogger:
    """SQLite database logger for structured data"""
    
    def __init__(self, db_path: str = "logs/motor_grid.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Motor states table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS motor_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_id TEXT,
                grid_x INTEGER,
                grid_y INTEGER,
                pico_id INTEGER,
                channel INTEGER,
                pulse_us INTEGER,
                intensity REAL
            )
        ''')
        
        # SPI packets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spi_packets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                pico_id INTEGER,
                packet_hex TEXT,
                motor_count INTEGER
            )
        ''')
        
        # Pattern execution table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                pattern_name TEXT,
                duration REAL,
                frames INTEGER,
                avg_fps REAL,
                spi_errors INTEGER
            )
        ''')
        
        self.conn.commit()
    
    def log_motor_state(self, motor_nodes: List[Any], session_id: str = ""):
        """Log motor states to database"""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        
        for motor in motor_nodes:
            cursor.execute('''
                INSERT INTO motor_states 
                (timestamp, session_id, grid_x, grid_y, pico_id, channel, pulse_us, intensity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, session_id, motor.grid_x, motor.grid_y, 
                  motor.pico_id, motor.channel, motor.current_pulse, motor.intensity))
        
        self.conn.commit()
    
    def log_spi_packet(self, pico_id: int, packet_hex: str, motor_count: int = 12):
        """Log SPI packet to database"""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO spi_packets (timestamp, pico_id, packet_hex, motor_count)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, pico_id, packet_hex, motor_count))
        
        self.conn.commit()
    
    def log_pattern_execution(self, stats: Dict):
        """Log pattern execution statistics"""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO pattern_executions 
            (timestamp, pattern_name, duration, frames, avg_fps, spi_errors)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, stats.get('pattern_name', 'unknown'),
              stats.get('actual_duration', 0),
              stats.get('frames_executed', 0),
              stats.get('actual_fps', 0),
              stats.get('spi_errors', 0)))
        
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        self.conn.close()