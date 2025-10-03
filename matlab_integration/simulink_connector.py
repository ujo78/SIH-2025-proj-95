"""
Simulink Connector Implementation

This module implements the SimulinkConnectorInterface for real-time
data exchange between the traffic simulation and Simulink models.
"""

import json
import socket
import struct
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import queue

from .interfaces import SimulinkConnectorInterface
from .config import MATLABConfig, SimulinkConfig


class SimulinkConnector(SimulinkConnectorInterface):
    """Implementation of real-time Simulink connectivity"""
    
    def __init__(self, config: Optional[MATLABConfig] = None):
        """Initialize Simulink connector with configuration"""
        self.config = config or MATLABConfig()
        self.simulink_config = self.config.simulink_config
        
        # Connection state
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.simulink_model = ""
        
        # Threading for real-time communication
        self.send_thread: Optional[threading.Thread] = None
        self.receive_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Data queues for thread-safe communication
        self.send_queue = queue.Queue(maxsize=self.simulink_config.buffer_size)
        self.receive_queue = queue.Queue(maxsize=self.simulink_config.buffer_size)
        
        # Time synchronization
        self.simulation_time = 0.0
        self.simulink_time = 0.0
        self.time_sync_enabled = self.simulink_config.enable_time_sync
        self.last_sync_time = time.time()
        
        # Callbacks for data handling
        self.data_received_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.connection_lost_callback: Optional[Callable[[], None]] = None
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.connection_errors = 0
    
    def establish_connection(self, simulink_model: str) -> bool:
        """Establish connection with Simulink model"""
        self.simulink_model = simulink_model
        
        try:
            # Create socket based on connection type
            if self.simulink_config.connection_type.lower() == 'tcp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.simulink_config.timeout)
                
                # Connect to Simulink
                address = (self.simulink_config.host_address, self.simulink_config.port)
                self.socket.connect(address)
                
            elif self.simulink_config.connection_type.lower() == 'udp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.settimeout(self.simulink_config.timeout)
                
                # For UDP, we'll bind to the port and send to the target
                self.socket.bind(('', self.simulink_config.port))
                
            else:
                raise ValueError(f"Unsupported connection type: {self.simulink_config.connection_type}")
            
            self.connected = True
            self.running = True
            
            # Start communication threads
            self._start_communication_threads()
            
            # Send initial handshake
            handshake_data = {
                'type': 'handshake',
                'model': simulink_model,
                'timestamp': datetime.now().isoformat(),
                'config': {
                    'streaming_frequency': self.simulink_config.streaming_frequency,
                    'time_sync_enabled': self.time_sync_enabled,
                    'data_format': 'binary' if self.simulink_config.use_binary_format else 'json'
                }
            }
            
            return self.send_real_time_data(handshake_data)
            
        except Exception as e:
            print(f"Failed to establish Simulink connection: {e}")
            self.connection_errors += 1
            self.connected = False
            return False
    
    def send_real_time_data(self, data: Dict[str, Any]) -> bool:
        """Send real-time simulation data to Simulink"""
        if not self.connected or not self.socket:
            return False
        
        try:
            # Add timestamp if requested
            if self.simulink_config.include_timestamps:
                data['timestamp'] = time.time()
                data['simulation_time'] = self.simulation_time
            
            # Prepare data for transmission
            if self.simulink_config.use_binary_format:
                message = self._encode_binary_message(data)
            else:
                message = json.dumps(data).encode('utf-8')
            
            # Add message to send queue
            if not self.send_queue.full():
                self.send_queue.put(message, block=False)
                return True
            else:
                print("Warning: Send queue is full, dropping message")
                return False
                
        except Exception as e:
            print(f"Error preparing data for Simulink: {e}")
            return False
    
    def receive_control_signals(self) -> Dict[str, Any]:
        """Receive control signals from Simulink model"""
        try:
            # Get message from receive queue (non-blocking)
            message = self.receive_queue.get(block=False)
            
            if self.simulink_config.use_binary_format:
                data = self._decode_binary_message(message)
            else:
                data = json.loads(message.decode('utf-8'))
            
            # Handle time synchronization
            if self.time_sync_enabled and 'simulink_time' in data:
                self.simulink_time = data['simulink_time']
                self._synchronize_time()
            
            return data
            
        except queue.Empty:
            return {}
        except Exception as e:
            print(f"Error receiving data from Simulink: {e}")
            return {}
    
    def synchronize_simulation_time(self, simulation_time: float) -> None:
        """Synchronize simulation time with Simulink"""
        self.simulation_time = simulation_time
        
        if self.time_sync_enabled:
            self._synchronize_time()
    
    def close_connection(self) -> None:
        """Close connection with Simulink model"""
        self.running = False
        self.connected = False
        
        # Stop communication threads
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=1.0)
        
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        
        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print(f"Simulink connection closed. Stats: Sent={self.messages_sent}, Received={self.messages_received}")
    
    def set_data_received_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback for when data is received from Simulink"""
        self.data_received_callback = callback
    
    def set_connection_lost_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for when connection is lost"""
        self.connection_lost_callback = callback
    
    def get_connection_statistics(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            'connected': self.connected,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'connection_errors': self.connection_errors,
            'send_queue_size': self.send_queue.qsize(),
            'receive_queue_size': self.receive_queue.qsize(),
            'simulation_time': self.simulation_time,
            'simulink_time': self.simulink_time
        }
    
    def _start_communication_threads(self) -> None:
        """Start threads for sending and receiving data"""
        self.send_thread = threading.Thread(target=self._send_worker, daemon=True)
        self.receive_thread = threading.Thread(target=self._receive_worker, daemon=True)
        
        self.send_thread.start()
        self.receive_thread.start()
    
    def _send_worker(self) -> None:
        """Worker thread for sending data to Simulink"""
        while self.running and self.connected:
            try:
                # Get message from queue with timeout
                message = self.send_queue.get(timeout=0.1)
                
                if self.simulink_config.connection_type.lower() == 'tcp':
                    # Send message length first, then message
                    length = struct.pack('!I', len(message))
                    self.socket.sendall(length + message)
                else:  # UDP
                    address = (self.simulink_config.host_address, self.simulink_config.port)
                    self.socket.sendto(message, address)
                
                self.messages_sent += 1
                
                # Rate limiting
                time.sleep(1.0 / self.simulink_config.streaming_frequency)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in send worker: {e}")
                self.connection_errors += 1
                if self.simulink_config.auto_reconnect:
                    self._attempt_reconnection()
                break
    
    def _receive_worker(self) -> None:
        """Worker thread for receiving data from Simulink"""
        while self.running and self.connected:
            try:
                if self.simulink_config.connection_type.lower() == 'tcp':
                    # Receive message length first
                    length_data = self._receive_exact(4)
                    if not length_data:
                        break
                    
                    message_length = struct.unpack('!I', length_data)[0]
                    message = self._receive_exact(message_length)
                    
                else:  # UDP
                    message, addr = self.socket.recvfrom(4096)
                
                if message:
                    if not self.receive_queue.full():
                        self.receive_queue.put(message, block=False)
                    
                    self.messages_received += 1
                    
                    # Call callback if set
                    if self.data_received_callback:
                        try:
                            if self.simulink_config.use_binary_format:
                                data = self._decode_binary_message(message)
                            else:
                                data = json.loads(message.decode('utf-8'))
                            self.data_received_callback(data)
                        except Exception as e:
                            print(f"Error in data callback: {e}")
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error in receive worker: {e}")
                self.connection_errors += 1
                if self.simulink_config.auto_reconnect:
                    self._attempt_reconnection()
                break
    
    def _receive_exact(self, num_bytes: int) -> Optional[bytes]:
        """Receive exact number of bytes from TCP socket"""
        data = b''
        while len(data) < num_bytes:
            chunk = self.socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def _encode_binary_message(self, data: Dict[str, Any]) -> bytes:
        """Encode message in binary format for efficient transmission"""
        # Simple binary encoding - can be enhanced for specific data types
        json_data = json.dumps(data).encode('utf-8')
        
        if self.simulink_config.data_compression:
            import zlib
            json_data = zlib.compress(json_data)
        
        return json_data
    
    def _decode_binary_message(self, message: bytes) -> Dict[str, Any]:
        """Decode binary message"""
        if self.simulink_config.data_compression:
            import zlib
            message = zlib.decompress(message)
        
        return json.loads(message.decode('utf-8'))
    
    def _synchronize_time(self) -> None:
        """Synchronize simulation time with Simulink"""
        current_time = time.time()
        
        # Check if synchronization is needed
        time_diff = abs(self.simulation_time - self.simulink_time)
        
        if time_diff > self.simulink_config.sync_tolerance:
            # Send time synchronization message
            sync_data = {
                'type': 'time_sync',
                'simulation_time': self.simulation_time,
                'system_time': current_time,
                'time_difference': time_diff
            }
            
            # Add to high priority (front of queue)
            try:
                # Clear old sync messages
                temp_queue = queue.Queue()
                while not self.send_queue.empty():
                    try:
                        msg = self.send_queue.get_nowait()
                        temp_queue.put(msg)
                    except queue.Empty:
                        break
                
                # Add sync message first
                if self.simulink_config.use_binary_format:
                    sync_message = self._encode_binary_message(sync_data)
                else:
                    sync_message = json.dumps(sync_data).encode('utf-8')
                
                self.send_queue.put(sync_message)
                
                # Re-add other messages
                while not temp_queue.empty():
                    try:
                        msg = temp_queue.get_nowait()
                        if not self.send_queue.full():
                            self.send_queue.put(msg)
                    except queue.Empty:
                        break
                        
            except Exception as e:
                print(f"Error during time synchronization: {e}")
        
        self.last_sync_time = current_time
    
    def _attempt_reconnection(self) -> None:
        """Attempt to reconnect to Simulink"""
        if not self.simulink_config.auto_reconnect:
            return
        
        for attempt in range(self.simulink_config.max_reconnect_attempts):
            print(f"Attempting reconnection {attempt + 1}/{self.simulink_config.max_reconnect_attempts}")
            
            time.sleep(self.simulink_config.reconnect_delay)
            
            # Close current connection
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            
            # Try to reconnect
            if self.establish_connection(self.simulink_model):
                print("Reconnection successful")
                return
        
        print("Reconnection failed")
        self.connected = False
        
        if self.connection_lost_callback:
            self.connection_lost_callback()