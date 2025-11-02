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
A1 = (500.000, -100.000)
G1 = (500.000, 100.000)
A8 = (300.000, -90.000)
G8 = (290.000, 105.000)

TEMP_CMD = "MJX286.878Y200.064Z433.700Rz0.018Ry180.000Rx0.016J70.00J80.00J90.00Sp30Ac15Dc15Rm80WFLm000000"
HOME = "MJX286.878Y0.064Z433.700Rz0.018Ry180.000Rx0.016J70.00J80.00J90.00Sp30Ac15Dc15Rm80WFLm000000"

# ===============================
# FUNGSI PEMBANTU
# ===============================

def wait_robot_response(max_wait=20):
    """
    Menunggu sampai robot mengirim respon (apapun isinya).
    Akan timeout setelah max_wait detik.
    """
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
    file = square[0].lower()
    rank = int(square[1])

    fx = (ord(file) - ord('a')) / (ord('g') - ord('a'))  # file A→G
    fy = (rank - 1) / (8 - 1)                            # rank 1→8

    x1 = A1[0] + (A8[0] - A1[0]) * fy
    x2 = G1[0] + (G8[0] - G1[0]) * fy
    y1 = A1[1] + (A8[1] - A1[1]) * fy
    y2 = G1[1] + (G8[1] - G1[1]) * fy

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
    send_robot(HOME, "Move HOME")

def gripper_open():
    print("> Gripper OPEN")
    gripper.write(b"SV0P60\n")
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
    move_robot(xs, ys, 240, 30, f"Ke atas {start}")
    move_robot(xs, ys, 150, 5, f"Turun ke {start}")
    gripper_close()
    move_robot(xs, ys, 240, 5, f"Naik dari {start}")
    move_temp()
    move_robot(xe, ye, 240, 30, f"Ke atas {end}")
    move_robot(xe, ye, 150, 5, f"Turun ke {end}")
    gripper_open()
    move_robot(xe, ye, 240, 5, f"Naik dari {end}")
    move_home()

    total_time = time.time() - total_start
    gripper_close()
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
