import os
import socket
import struct
import time
import select

def calculate_checksum(data):
    total = 0
    count = (len(data) // 2) * 2
    i = 0

    while i < count:
        value = data[i + 1] * 256 + data[i]
        total += value
        total &= 0xffffffff
        i += 2

    if i < len(data):
        total += data[-1]
        total &= 0xffffffff

    total = (total >> 16) + (total & 0xffff)
    total += (total >> 16)
    result = ~total & 0xffff
    return (result >> 8) | ((result << 8) & 0xff00)


def build_icmp_packet(identifier, sequence):
    header = struct.pack('bbHHh', 8, 0, 0, identifier, sequence)
    payload = b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    checksum_value = calculate_checksum(header + payload)
    header = struct.pack('bbHHh', 8, 0, socket.htons(checksum_value), identifier, sequence)
    return header + payload


def ping(destination, ttl_value, timeout_value=2):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl_value)
        sock.settimeout(timeout_value)
    except socket.error as err:
        print(f"Ошибка создания сокета: {err}")
        return None, None

    packet_id = os.getpid() & 0xFFFF
    packet_seq = 1
    packet = build_icmp_packet(packet_id, packet_seq)

    try:
        sock.sendto(packet, (destination, 0))
        send_time = time.time()
    except socket.error as err:
        print(f"Ошибка отправки пакета: {err}")
        sock.close()
        return None, None

    while True:
        try:
            ready = select.select([sock], [], [], timeout_value)
            if not ready[0]:
                print("Превышено время ожидания ответа.")
                sock.close()
                return None, None

            receive_time = time.time()
            packet_recv, addr_recv = sock.recvfrom(1024)
            icmp_header_recv = packet_recv[20:28]
            type_recv, code_recv, checksum_recv, id_recv, seq_recv = struct.unpack('bbHHh', icmp_header_recv)

            if type_recv == 0 and id_recv == packet_id:
                sock.close()
                return addr_recv[0], (receive_time - send_time) * 1000
            elif type_recv == 11 and code_recv == 0:
                sock.close()
                return addr_recv[0], (receive_time - send_time) * 1000
        except socket.error as err:
            print(f"Ошибка получения ответа: {err}")
            sock.close()
            return None, None


def perform_tracert(target, max_hops=30, packets_per_hop=3):
    print(f"Трассировка маршрута к {target} (максимум {max_hops} переходов):")
    for hop in range(1, max_hops + 1):
        times = []
        ip = None
        for _ in range(packets_per_hop):
            addr, duration = ping(target, hop)
            if addr:
                ip = addr
                times.append(f"{duration:.2f} мс")
            else:
                times.append("*")

        if ip:
            print(f"{hop}\t{ip}\t{times[0]}\t{times[1]}\t{times[2]}")
            if ip == target:
                print("Узел достигнут.")
                return
        else:
            print(f"{hop}\t*\t*\t*\t*")

if __name__ == "__main__":
    target_ip = input("Введите IP-адрес: ")
    perform_tracert(target_ip)