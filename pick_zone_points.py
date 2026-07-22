import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import sys
import os

def main():
    image_path = "test_frame.png"
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found. Run extract_frame.py first.")
        sys.exit(1)

    img = mpimg.imread(image_path)
    fig, ax = plt.subplots()
    ax.imshow(img)
    plt.title("Click 4 corners of your restricted zone, in order (e.g., clockwise). Close window when done.")

    points = []

    def onclick(event):
        if event.xdata is not None and event.ydata is not None:
            x, y = int(event.xdata), int(event.ydata)
            points.append((x, y))
            print(f"Point {len(points)}: ({x}, {y})")
            ax.plot(x, y, 'ro')
            fig.canvas.draw()

    fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()

    print("\nFinal polygon (paste this back into the chat):")
    print(f"[[{points[0][0]}, {points[0][1]}], [{points[1][0]}, {points[1][1]}], [{points[2][0]}, {points[2][1]}], [{points[3][0]}, {points[3][1]}]]" if len(points) == 4 else points)

if __name__ == "__main__":
    main()
