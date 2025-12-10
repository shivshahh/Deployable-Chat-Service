#!/usr/bin/env python3
"""
Load testing script for the chat server.

Usage:
    python3 load_test.py [options]

Options:
    --host HOST          Server host (default: localhost)
    --port PORT          Server port (default: 8888)
    --clients N          Number of concurrent clients (default: 10)
    --messages N         Messages per client (default: 10)
    --delay SECONDS      Delay between messages in seconds (default: 0.1)
    --test-type TYPE     Test type: 'direct', 'broadcast', or 'mixed' (default: mixed)
    --duration SECONDS   Test duration in seconds (default: 30)
"""

import socket
import threading
import time
import argparse
import statistics
from collections import defaultdict
from datetime import datetime

class LoadTestClient:
    def __init__(self, client_id, host, port, recipient, test_type, messages, delay):
        self.client_id = client_id
        self.username = f"client_{client_id}"
        self.host = host
        self.port = port
        self.recipient = recipient
        self.test_type = test_type
        self.messages = messages
        self.delay = delay
        self.sock = None
        self.connected = False
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0,
            'latencies': [],
            'connection_time': None,
            'start_time': None,
            'end_time': None
        }
        self.running = False

    def connect(self):
        """Connect to the server and send initial handshake."""
        try:
            start = time.time()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)  # 10 second timeout
            self.sock.connect((self.host, self.port))
            
            # Send handshake: username--recipient
            handshake = f"{self.username}--{self.recipient}"
            self.sock.sendall(handshake.encode('utf-8'))
            
            self.stats['connection_time'] = time.time() - start
            self.connected = True
            return True
        except Exception as e:
            print(f"[{self.username}] Connection error: {e}")
            self.stats['errors'] += 1
            self.connected = False
            return False

    def receive_messages(self):
        """Thread function to receive messages from server."""
        buffer = ""
        while self.running and self.connected:
            try:
                data = self.sock.recv(1024).decode('utf-8')
                if not data:
                    self.connected = False
                    break
                
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        if line == "HISTORY_END":
                            continue
                        self.stats['messages_received'] += 1
            except socket.timeout:
                continue
            except (OSError, BrokenPipeError, ConnectionResetError) as e:
                self.connected = False
                break
            except Exception as e:
                if self.running:
                    # Only print non-connection errors
                    if not isinstance(e, (OSError, BrokenPipeError, ConnectionResetError)):
                        print(f"[{self.username}] Receive error: {e}")
                    self.stats['errors'] += 1
                self.connected = False
                break

    def send_messages(self):
        """Send messages to the server."""
        self.stats['start_time'] = time.time()
        
        for i in range(self.messages):
            if not self.running or not self.connected:
                break
                
            message = f"Test message {i+1} from {self.username}"
            start = time.time()
            
            try:
                if self.sock and self.connected:
                    self.sock.sendall((message + '\n').encode('utf-8'))
                    self.stats['messages_sent'] += 1
                    
                    # Measure round-trip latency (approximate)
                    latency = time.time() - start
                    self.stats['latencies'].append(latency)
            except (OSError, BrokenPipeError, ConnectionResetError):
                # Connection closed, stop sending
                self.connected = False
                self.stats['errors'] += 1
                break
            except Exception as e:
                # Other errors - log but continue
                self.stats['errors'] += 1
                if self.connected:  # Only log if we thought we were connected
                    print(f"[{self.username}] Send error: {e}")
                self.connected = False
                break
            
            if self.delay > 0:
                time.sleep(self.delay)
        
        self.stats['end_time'] = time.time()

    def run(self):
        """Run the load test for this client."""
        if not self.connect():
            return
        
        self.running = True
        
        # Start receiver thread
        receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receiver_thread.start()
        
        # Wait a bit for history to be received
        time.sleep(0.5)
        
        # Send messages
        self.send_messages()
        
        # Wait a bit for final messages
        time.sleep(1)
        
        self.running = False
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass

class LoadTester:
    def __init__(self, host, port, num_clients, messages_per_client, delay, test_type, duration):
        self.host = host
        self.port = port
        self.num_clients = num_clients
        self.messages_per_client = messages_per_client
        self.delay = delay
        self.test_type = test_type
        self.duration = duration
        self.clients = []
        self.results = {
            'total_clients': 0,
            'successful_clients': 0,
            'failed_clients': 0,
            'total_messages_sent': 0,
            'total_messages_received': 0,
            'total_errors': 0,
            'connection_times': [],
            'latencies': [],
            'test_duration': 0
        }

    def determine_recipient(self, client_id):
        """Determine recipient based on test type."""
        if self.test_type == 'broadcast':
            return "BROADCAST"
        elif self.test_type == 'direct':
            # Pair clients: 0->1, 2->3, etc.
            if client_id % 2 == 0:
                return f"client_{client_id + 1}"
            else:
                return f"client_{client_id - 1}"
        else:  # mixed
            # Alternate between direct and broadcast
            if client_id % 3 == 0:
                return "BROADCAST"
            else:
                return f"client_{(client_id + 1) % self.num_clients}"

    def run_test(self):
        """Run the load test."""
        print(f"\n{'='*60}")
        print(f"Starting Load Test")
        print(f"{'='*60}")
        print(f"Host: {self.host}")
        print(f"Port: {self.port}")
        print(f"Clients: {self.num_clients}")
        print(f"Messages per client: {self.messages_per_client}")
        print(f"Delay between messages: {self.delay}s")
        print(f"Test type: {self.test_type}")
        print(f"Duration: {self.duration}s")
        print(f"{'='*60}\n")

        start_time = time.time()
        
        # Create and start all clients
        threads = []
        for i in range(self.num_clients):
            recipient = self.determine_recipient(i)
            client = LoadTestClient(
                i, self.host, self.port, recipient,
                self.test_type, self.messages_per_client, self.delay
            )
            self.clients.append(client)
            
            thread = threading.Thread(target=client.run)
            thread.start()
            threads.append(thread)
            
            # Stagger connections slightly
            time.sleep(0.01)

        # Wait for all threads to complete or duration expires
        if self.duration > 0:
            time.sleep(self.duration)
            # Signal all clients to stop
            for client in self.clients:
                client.running = False
        else:
            for thread in threads:
                thread.join()

        # Collect results
        self.collect_results()
        self.results['test_duration'] = time.time() - start_time

    def collect_results(self):
        """Collect statistics from all clients."""
        for client in self.clients:
            self.results['total_clients'] += 1
            
            if client.stats['connection_time'] is not None:
                self.results['successful_clients'] += 1
                self.results['connection_times'].append(client.stats['connection_time'])
            else:
                self.results['failed_clients'] += 1
            
            self.results['total_messages_sent'] += client.stats['messages_sent']
            self.results['total_messages_received'] += client.stats['messages_received']
            self.results['total_errors'] += client.stats['errors']
            self.results['latencies'].extend(client.stats['latencies'])

    def print_results(self):
        """Print test results."""
        print(f"\n{'='*60}")
        print(f"Load Test Results")
        print(f"{'='*60}")
        print(f"Test Duration: {self.results['test_duration']:.2f}s")
        print(f"\nClients:")
        print(f"  Total: {self.results['total_clients']}")
        print(f"  Successful: {self.results['successful_clients']}")
        print(f"  Failed: {self.results['failed_clients']}")
        
        if self.results['connection_times']:
            print(f"\nConnection Times:")
            print(f"  Average: {statistics.mean(self.results['connection_times'])*1000:.2f}ms")
            print(f"  Min: {min(self.results['connection_times'])*1000:.2f}ms")
            print(f"  Max: {max(self.results['connection_times'])*1000:.2f}ms")
            if len(self.results['connection_times']) > 1:
                print(f"  Std Dev: {statistics.stdev(self.results['connection_times'])*1000:.2f}ms")
        
        print(f"\nMessages:")
        print(f"  Sent: {self.results['total_messages_sent']}")
        print(f"  Received: {self.results['total_messages_received']}")
        print(f"  Errors: {self.results['total_errors']}")
        
        if self.results['latencies']:
            print(f"\nMessage Latency:")
            print(f"  Average: {statistics.mean(self.results['latencies'])*1000:.2f}ms")
            print(f"  Min: {min(self.results['latencies'])*1000:.2f}ms")
            print(f"  Max: {max(self.results['latencies'])*1000:.2f}ms")
            if len(self.results['latencies']) > 1:
                print(f"  Std Dev: {statistics.stdev(self.results['latencies'])*1000:.2f}ms")
                print(f"  Median: {statistics.median(self.results['latencies'])*1000:.2f}ms")
                # Percentiles
                sorted_latencies = sorted(self.results['latencies'])
                p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
                p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
                p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
                print(f"  P50: {p50*1000:.2f}ms")
                print(f"  P95: {p95*1000:.2f}ms")
                print(f"  P99: {p99*1000:.2f}ms")
        
        if self.results['test_duration'] > 0:
            throughput = self.results['total_messages_sent'] / self.results['test_duration']
            print(f"\nThroughput:")
            print(f"  Messages/sec: {throughput:.2f}")
        
        print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(
        description='Load test script for chat server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8888, help='Server port (default: 8888)')
    parser.add_argument('--clients', type=int, default=10, help='Number of concurrent clients (default: 10)')
    parser.add_argument('--messages', type=int, default=10, help='Messages per client (default: 10)')
    parser.add_argument('--delay', type=float, default=0.1, help='Delay between messages in seconds (default: 0.1)')
    parser.add_argument('--test-type', choices=['direct', 'broadcast', 'mixed'], default='mixed',
                       help='Test type: direct, broadcast, or mixed (default: mixed)')
    parser.add_argument('--duration', type=int, default=0,
                       help='Test duration in seconds (0 = run until all messages sent, default: 0)')
    
    args = parser.parse_args()
    
    tester = LoadTester(
        args.host,
        args.port,
        args.clients,
        args.messages,
        args.delay,
        args.test_type,
        args.duration
    )
    
    try:
        tester.run_test()
        tester.print_results()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        tester.print_results()
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

