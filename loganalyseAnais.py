import argparse
import abc
import re
import time
from datetime import datetime


# Observer base class


class LogObserver(abc.ABC):
    """Abstract base class for log observers."""
    
    @abc.abstractmethod
    def update(self, log_line: str, timestamp: str, level: str, message: str) -> None:
        """Update method called by LogAnalyzer when a new log line is analyzed."""
        pass



# Concrete Observers

class ErrorObserver(LogObserver):
    """Observer for ERROR messages."""
    
    def update(self, log_line: str, timestamp: str, level: str, message: str) -> None:
        if level == "ERROR":
            print(f"[ERROR OBSERVER] {timestamp} - {message}")


class WarningObserver(LogObserver):
    """Observer for WARN messages."""
    
    def update(self, log_line: str, timestamp: str, level: str, message: str) -> None:
        if level == "WARN":
            print(f"[WARNING OBSERVER] {timestamp} - {message}")


class UserActivityObserver(LogObserver):
    """Observer for messages involving users."""
    
    def update(self, log_line: str, timestamp: str, level: str, message: str) -> None:
        # Check if message contains "user" or "User"
        if re.search(r"\buser\b", message, re.IGNORECASE):
            # Extract username if available
            user_match = re.search(r"\buser[=:\s]+(\w+)", message, re.IGNORECASE)
            username = user_match.group(1) if user_match else "unknown"
            print(f"[USER ACTIVITY OBSERVER] {timestamp} - User: {username} - {message}")



# Subject class (LogAnalyzer)

class LogAnalyzer:
    """Subject class that notifies observers of log events."""
    
    def __init__(self, filepath: str, n_lines: int, acc_factor: float):
        self.filepath = filepath
        self.n_lines = n_lines
        self.acc_factor = acc_factor
        self._observers = []
        
        # Regex pattern for parsing log lines: YYYY-MM-DD HH:MM:SS
        self.timestamp_pattern = re.compile(r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})")
        
        # Regex pattern for log level
        self.level_pattern = re.compile(r"\b(ERROR|WARN|WARNING|INFO)\b")
    
    def attach(self, observer: LogObserver) -> None:
        """Register an observer."""
        self._observers.append(observer)
        print(f"Attached {observer.__class__.__name__} to {self.__class__.__name__}")
    
    def detach(self, observer: LogObserver) -> None:
        """Unregister an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
            print(f"Detached {observer.__class__.__name__} from {self.__class__.__name__}")
    
    def notify(self, log_line: str, timestamp: str, level: str, message: str) -> None:
        """Notify all observers with log information."""
        for observer in self._observers:
            observer.update(log_line, timestamp, level, message)
    
    def parse_line(self, log_line: str) -> tuple:
        """Parse a log line and extract timestamp, level, and message."""
        # Extract timestamp
        timestamp_match = self.timestamp_pattern.search(log_line)
        timestamp = timestamp_match.group(1) if timestamp_match else "unknown"
        
        # Extract log level
        level_match = self.level_pattern.search(log_line)
        level = level_match.group(1) if level_match else "INFO"
        
        # Get the message (everything after the timestamp and level)
        message = log_line.strip()
        
        return timestamp, level, message
    
    def analyze_line(self, log_line: str) -> None:
        """Analyze a log line and notify observers."""
        timestamp, level, message = self.parse_line(log_line)
        self.notify(log_line, timestamp, level, message)
    
    def run(self) -> None:
        """Read and process log lines from file with time simulation."""
        previous_timestamp = None
        line_count = 0
        
        try:
            with open(self.filepath, 'r') as f:
                for line in f:
                    # Stop if we've reached the limit
                    if self.n_lines > 0 and line_count >= self.n_lines:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse timestamp from the log line
                    timestamp_match = self.timestamp_pattern.search(line)
                    if not timestamp_match:
                        continue
                    
                    current_timestamp_str = timestamp_match.group(1)
                    
                    # For the first line, process immediately
                    if previous_timestamp is None:
                        self.analyze_line(line)
                    else:
                        # Calculate wait time based on timestamps
                        try:
                            current_time = datetime.strptime(current_timestamp_str, "%Y-%m-%d %H:%M:%S")
                            previous_time = datetime.strptime(previous_timestamp, "%Y-%m-%d %H:%M:%S")
                            wait_seconds = (current_time - previous_time).total_seconds()
                            
                            # Apply acceleration factor
                            wait_seconds = wait_seconds / self.acc_factor
                            
                            # Wait before processing
                            if wait_seconds > 0:
                                time.sleep(wait_seconds)
                        except ValueError:
                            pass
                        
                        # Analyze the line
                        self.analyze_line(line)
                    
                    previous_timestamp = current_timestamp_str
                    line_count += 1
                    
        except FileNotFoundError:
            print(f"Error: File '{self.filepath}' not found.")
        except Exception as e:
            print(f"Error reading file: {e}")



# Argument parsing

def parse_args():
    parser = argparse.ArgumentParser(description="Analyse de logs")
    parser.add_argument("--input", "-i", required=True, help="Chemin vers le fichier de logs à analyser")
    parser.add_argument("-n", required=True, type=int, help="Nombre de lignes à analyser")
    parser.add_argument("--acc", type=float, default=1.0, help="Facteur d'accélération")
    return parser.parse_args()



# Main function

if __name__ == "__main__":
    args = parse_args()
    
    # Create LogAnalyzer instance
    analyzer = LogAnalyzer(args.input, args.n, args.acc)
    
    # Attach observers
    analyzer.attach(ErrorObserver())
    analyzer.attach(WarningObserver())
    analyzer.attach(UserActivityObserver())
    
    # Run the analysis
    analyzer.run()