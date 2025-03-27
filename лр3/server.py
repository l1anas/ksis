import socket
import sys

class Server:
    def __init__(self):
        self.ip = self.get_valid_ip()
        self.port = self.get_valid_port()
        self.clients = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            self.sock.bind((self.ip, self.port))
            print(f"\nСервер запущен на {self.ip}:{self.port}")
            print("Ожидание подключений\n")
        except socket.error as e:
            print(f"Ошибка привязки к {self.ip}:{self.port}: {e}")
            sys.exit(1)

    def get_valid_ip(self):
        while True:
            ip = input("Введите IP сервера (или Enter для localhost): ").strip()
            if not ip:
                return '127.0.0.1'
            try:
                socket.inet_aton(ip)
                return ip
            except socket.error:
                print("Некорректный IP-адрес")

    def get_valid_port(self):
        while True:
            try:
                port = int(input("Введите порт сервера (1024-65535): "))
                if 1024 <= port <= 65535:
                    return port
                print("Порт должен быть в диапазоне 1024-65535")
            except ValueError:
                print("Введите число")

    def broadcast(self, message, sender_addr=None):
        for addr, (name, _, _) in self.clients.items():
            if addr != sender_addr:
                try:
                    self.sock.sendto(message.encode(), addr)
                except socket.error as e:
                    print(f"Ошибка отправки {name}: {e}")
                    del self.clients[addr]

    def run(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                data = data.decode()
                # Новое подключение
                if addr not in self.clients:
                    if data.startswith("reg:"):
                        name = data.split(":")[1]
                        self.clients[addr] = (name, addr[0], addr[1])
                        print(f"{name} подключился ({addr[0]}:{addr[1]})")
                        self.broadcast(f"Пользователь {name} вошел в чат", addr)
                        continue
                # Отключение клиента
                if data.lower() == 'exit':
                    name = self.clients[addr][0]
                    del self.clients[addr]
                    print(f"{name} отключился")
                    self.broadcast(f"Пользователь {name} вышел из чата", addr)
                    continue

                # Обычное сообщение
                name = self.clients[addr][0]
                message = f"{name}: {data}"
                print(message)
                self.broadcast(message, addr)

            except Exception as e:
                print(f"Ошибка: {e}")

if __name__ == "__main__":
    server = Server()
    server.run()