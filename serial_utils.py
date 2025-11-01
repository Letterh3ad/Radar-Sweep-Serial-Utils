import serial
import sys
import glob

BAUD = 9600

def list_serial_ports():
    """Return a list of all possible serial ports for the current OS."""
    if sys.platform.startswith("win"):
        # Windows COM ports (COM0–COM9)
        return [f"COM{i}" for i in range(10)]

    elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
        # Linux: search for all likely serial device paths
        patterns = ("/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyS*")
        ports = []
        for pattern in patterns:
            ports.extend(glob.glob(pattern))
        return ports



    else:
        raise EnvironmentError("Unsupported operating system")


def find_serial_port(baud=BAUD):
    """Try all ports and return the first open serial object."""
    for dev in list_serial_ports():
        try:
            ser = serial.Serial(dev, baud, timeout=0.1)
            if ser.is_open:
                print(f"Port {dev} open")
                return ser
        except serial.SerialException:
            print(f"Port {dev} checked - no response")
    print("No available serial ports found.")
    return None

def read_serial(ser, output_file=None):
    """
    Continuously read lines from the serial port.
    Optionally write received data to a text file.

    Args:
        ser (serial.Serial): Open serial object.
        output_file (str, optional): File path to write incoming data.
    """
    if ser is None or not ser.is_open:
        print("Serial port not open.")
        return

    file_handle = open(output_file, "a") if output_file else None

    print("Reading from serial port. Press Ctrl+C to stop.")
    try:
        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode(errors="ignore").strip()
                if data:
                    print(f"Received: {data}")
                    if file_handle:
                        file_handle.write(data + "\n")
                        file_handle.flush()
    except KeyboardInterrupt:
        print("\n Stopped reading.")
    finally:
        if file_handle:
            file_handle.close()
        ser.close()
        print("Serial port closed.")


def write_serial(ser, message):
    """
    Write a message to the serial port.

    Args:
        ser (serial.Serial): Open serial object.
        message (str): Text to send.
    """
    if ser and ser.is_open:
        ser.write((message + "\n").encode())
        print(f"Sent: {message}")
    else:
        print("Serial port not open.")

if __name__ == "__main__":
    ser = find_serial_port(BAUD)
    if ser:
        # Example usage: write and read loop
        write_serial(ser, "Hello device!")
        read_serial(ser, output_file="Data_File.txt")
