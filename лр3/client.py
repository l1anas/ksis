import socket
import sys
from threading import Thread, Event
import time

class Client:
    def __init__(self):
        self.name = input("Введите ваше имя: ").strip()
        self.server_ip = self.get_valid_ip()
        self.server_port = self.get_valid_port("сервера")
        self.client_port = self.get_valid_port("клиента")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.stop_event = Event()
        try:
            self.sock.bind(('', self.client_port))
            print(f"\n{self.name}, вы подключены на порту {self.client_port}")
            print("Введите сообщение (или 'exit' для выхода):\n")
        except socket.error as e:
            print(f"Ошибка привязки к порту {self.client_port}: {e}")
            sys.exit(1)

    def get_valid_ip(self):
        while True:
            ip = input("Введите IP сервера: ").strip()
            parts = ip.split(".")
            if len(parts) != 4:
                print("IP должен содержать 4 октета")
                continue
            try:
                if not all(0 <= int(part) <= 255 for part in parts):
                    print("Каждый октет IP должен быть 0-255")
                    continue
                return ip
            except ValueError:
                print("Некорректный IP-адрес")

    def get_valid_port(self, target):
        while True:
            try:
                port = int(input(f"Введите порт {target} (1024-65535): "))
                if 1024 <= port <= 65535:
                    return port
                print("Порт должен быть в диапазоне 1024-65535")
            except ValueError:
                print("Введите число")

    def receive_messages(self):
        while not self.stop_event.is_set():
            try:
                data, _ = self.sock.recvfrom(1024)
                print(data.decode())
            except socket.error as e:
                if not self.stop_event.is_set():
                    print(f"\nСоединение прервано: {e}")
                break

    def run(self):
        receiver = Thread(target=self.receive_messages, daemon=True)
        receiver.start()

        self.sock.sendto(f"reg:{self.name}".encode(), (self.server_ip, self.server_port))

        try:
            while True:
                message = input()
                if not message:
                    continue
                if message.lower() == 'exit':
                    self.sock.sendto(b'exit', (self.server_ip, self.server_port))
                    break
                self.sock.sendto(message.encode(), (self.server_ip, self.server_port))
        finally:
            self.stop_event.set()
            time.sleep(0.1)
            self.sock.close()
            print("\nОтключение от сервера")

if __name__ == "__main__":
    client = Client()
    client.run()