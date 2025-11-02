import serial
import time

# ===============================
# KONFIGURASI SERIAL
# ===============================
ROBOT_PORT = "COM16"      # ganti sesuai port robot
GRIPPER_PORT = "COM17"    # ganti sesuai port gripper
BAUDRATE = 9600

robot = serial.Serial(ROBOT_PORT, BAUDRATE, timeout=0.5)
gripper = serial.Serial(GRIPPER_PORT, BAUDRATE, timeout=0.5)

# ===============================
# POSISI REFERENSI
# ===============================
# Gunakan A1, H1, A8, H8
A1 = (500.000, -95.000)
H1 = (500.000, 95.000)
A8 = (300.000, -90.000)
H8 = (295.000, 105.000)

TEMP_CMD = "MJX286.878Y200.064Z433.700Rz0.018Ry180.000Rx0.016J70.00J80.00J90.00Sp35Ac15Dc15Rm80WFLm000000"
HOME_CMD = "MJX286.878Y0.064Z433.700Rz0.018Ry180.000Rx0.016J70.00J80.00J90.00Sp35Ac15Dc15Rm80WFLm000000"

# ===============================
# FUNGSI PEMBANTU
# ===============================

def wait_robot_response(max_wait=20):
    """Menunggu sampai robot mengirim respon (apapun isinya)."""
    start = time.time()
    buffer = ""
    while True:
        if robot.in_waiting:
            data = robot.read(robot.in_waiting).decode(errors='ignore')
            buffer += data
            if buffer.strip() != "":
                break
        if time.time() - start > max_wait:
            print("   ⚠️ Timeout: tidak ada respon dari robot (lanjut)...")
            break
        time.sleep(0.05)

    dur = time.time() - start
    print(f"   ↳ Respon diterima ({dur:.2f} detik)")
    return dur

def wait_gripper_response():
    """Gripper tidak kirim respon, tunggu singkat saja"""
    time.sleep(0.3)

def square_to_coord(square):
    """Mengubah notasi seperti 'e2' menjadi koordinat X,Y berdasarkan A1,H1,A8,H8"""
    file = square[0].lower()
    rank = int(square[1])

    # pastikan semua petak A–H tercover
    fx = (ord(file) - ord('a')) / (ord('h') - ord('a'))  # file A→H
    fy = (rank - 1) / (8 - 1)                            # rank 1→8

    # interpolasi linear antara tepi kiri dan kanan papan
    x1 = A1[0] + (A8[0] - A1[0]) * fy
    x2 = H1[0] + (H8[0] - H1[0]) * fy
    y1 = A1[1] + (A8[1] - A1[1]) * fy
    y2 = H1[1] + (H8[1] - H1[1]) * fy

    X = x1 + (x2 - x1) * fx
    Y = y1 + (y2 - y1) * fx
    return (X, Y)

def send_robot(cmd, note=""):
    print(f"> {note} ...")
    start = time.time()
    robot.write((cmd + "\n").encode())
    wait_robot_response()
    total = time.time() - start
    print(f"   ✓ {note} selesai ({total:.2f} detik)")

def move_robot(x, y, z=240, sp=30, note="Move"):
    cmd = f"MJX{x:.3f}Y{y:.3f}Z{z:.3f}Rz0.024Ry174.670Rx0.016J70.00J80.00J90.00Sp{sp}Ac15Dc15Rm80WFLm000000"
    send_robot(cmd, note)

def move_temp():
    send_robot(TEMP_CMD, "Move TEMP")

def move_home():
    send_robot(HOME_CMD, "Move HOME")

def gripper_open():
    print("> Gripper OPEN")
    gripper.write(b"SV0P35\n")
    wait_gripper_response()
    print("   ✓ Gripper OPEN selesai")

def gripper_close():
    print("> Gripper CLOSE")
    gripper.write(b"SV0P0\n")
    wait_gripper_response()
    print("   ✓ Gripper CLOSE selesai")

# ===============================
# GERAKAN UTAMA
# ===============================

def move_piece(move_str):
    start = move_str[:2]
    end = move_str[2:]

    print(f"\n=== Langkah {start} → {end} ===")
    xs, ys = square_to_coord(start)
    xe, ye = square_to_coord(end)

    total_start = time.time()

    gripper_open()
    move_temp()
    move_robot(xs, ys, 240, 45, f"Ke atas {start}")
    move_robot(xs, ys, 150, 10, f"Turun ke {start}")
    time.sleep(1)
    gripper_close()
    time.sleep(3)
    move_robot(xs, ys, 240, 20, f"Naik dari {start}")
    move_temp()
    move_robot(xe, ye, 240, 45, f"Ke atas {end}")
    move_robot(xe, ye, 150, 5, f"Turun ke {end}")
    gripper_open()
    move_robot(xe, ye, 240, 20, f"Naik dari {end}")
    move_home()
    gripper_close()

    total_time = time.time() - total_start
    print(f"=== Selesai dalam {total_time:.2f} detik ===\n")

# ===============================
# MAIN LOOP
# ===============================

if __name__ == "__main__":
    print("=== Robot Chess Controller ===")
    print("Masukkan langkah (contoh e2e4), atau 'q' untuk keluar.\n")

    while True:
        cmd = input("Langkah: ").strip()
        if cmd.lower() == "q":
            print("Keluar...")
            break
        if len(cmd) == 4:
            move_piece(cmd)
        else:
            print("Format salah, contoh: e2e4")
