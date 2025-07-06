import math

def main():
    try:
        width = float(input("Enter the width in cm: "))
        angle_deg = float(input("Enter the rotation angle in degrees: "))
        angle_rad = math.radians(angle_deg)

        if math.cos(angle_rad) == 0:
            print("Error: angle results in division by zero.")
            return

        required_length = width / math.cos(angle_rad)
        print("Required length: {:.4f} cm".format(required_length))

    except ValueError:
        print("Invalid input. Please enter numeric values.")

if __name__ == "__main__":
    main()

