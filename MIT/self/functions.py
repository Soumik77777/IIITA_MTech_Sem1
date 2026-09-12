import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

def get_system():
    dim = int(input("Enter dimension (2 or 3): "))

    if dim not in [2, 3]:
        raise ValueError("Dimension must be 2 or 3.")

    n = dim  # Setting number of equations = number of variables at this point

    print(f"\nEnter the coefficients of A ({n} x {dim}):")

    A, b = [], []

    for i in range(n):
        row = []

        print(f"\nEquation {i+1}:")

        for j in range(dim):
            coeff = float(
                input(f"Enter coefficient a{i+1}{j+1}: ")
            )
            row.append(coeff)
        A.append(row)

        rhs = float(
            input(f"Enter RHS b{i+1}: ")
        )
        b.append(rhs)

        if dim == 2:
            print(f"    ({row[0]}* x1) + ({row[1]}* x2) = {rhs}")
        else:
            print(f"    ({row[0]}* x1) + ({row[1]}* x2) + ({row[1]}* x3) = {rhs}")

    return np.array(A), np.array(b)


def plot_vectors_2x2(A, b):
    dim = A.shape[1]

    fig = plt.figure(figsize=(9, 4))

    if dim == 2:

        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)

        colors = ["red", "blue"]

        # ==================================================
        # LEFT: ROW PICTURE
        # ==================================================

        for i in range(2):

            row = A[i, :]
            x, y = row

            # Row vector
            ax1.quiver(
                0, 0, x, y,
                angles="xy",
                scale_units="xy",
                scale=1,
                color=colors[i],
                label=f"Row {i+1}"
            )

            # Perpendicular projections
            ax1.plot(
                [x, x], [0, y],
                color=colors[i],
                linestyle="--",
                linewidth=0.8
            )

            ax1.plot(
                [0, x], [y, y],
                color=colors[i],
                linestyle="--",
                linewidth=0.8
            )

            # Coordinate label at arrowhead
            ax1.text(
                x, y,
                f"({x:g}, {y:g})",
                color=colors[i],
                fontsize=10,
                ha="left",
                va="bottom"
            )

        ax1.axhline(0, color="black", linewidth=0.5)
        ax1.axvline(0, color="black", linewidth=0.5)

        limit = max(
            np.max(np.abs(A)),
            np.max(np.abs(b))
        ) * 1.2

        ax1.set_xlim(-limit, limit)
        ax1.set_ylim(-limit, limit)

        ax1.set_xlabel("x")
        ax1.set_ylabel("y")

        ax1.set_title("Row Picture")
        ax1.legend()
        ax1.grid()

        ax1.set_aspect("equal")

        # ==================================================
        # RIGHT: COLUMN PICTURE
        # ==================================================

        for i in range(2):

            col = A[:, i]
            x, y = col

            # Column vector
            ax2.quiver(
                0, 0, x, y,
                angles="xy",
                scale_units="xy",
                scale=1,
                color=colors[i],
                label=f"Column {i+1}"
            )

            # Perpendicular projections
            ax2.plot(
                [x, x], [0, y],
                color=colors[i],
                linestyle="--",
                linewidth=0.8
            )

            ax2.plot(
                [0, x], [y, y],
                color=colors[i],
                linestyle="--",
                linewidth=0.8
            )

            # Coordinate label at arrowhead
            ax2.text(
                x, y,
                f"({x:g}, {y:g})",
                color=colors[i],
                fontsize=10,
                ha="left",
                va="bottom"
            )

        # Vector b
        ax2.quiver(
            0, 0, b[0], b[1],
            angles="xy",
            scale_units="xy",
            scale=1,
            color="green",
            label="b"
        )

        # Perpendicular projections
        ax2.plot(
            [b[0], b[0]], [0, b[1]],
            color=colors[i],
            linestyle="--",
            linewidth=0.8
        )

        ax2.plot(
            [0, b[0]], [b[1], b[1]],
            color=colors[i],
            linestyle="--",
            linewidth=0.8
        )

        ax2.text(
            b[0], b[1],
            f"({b[0]:g}, {b[1]:g})",
            color="green",
            fontsize=10,
            ha="left",
            va="bottom"
        )

        ax2.axhline(0, color="black", linewidth=0.5)
        ax2.axvline(0, color="black", linewidth=0.5)

        ax2.set_xlim(-limit, limit)
        ax2.set_ylim(-limit, limit)

        ax2.set_xlabel("x")
        ax2.set_ylabel("y")

        ax2.set_title("Column Picture: A x = b")
        ax2.legend()
        ax2.grid()

        ax2.set_aspect("equal")

    else:
        print("Only 2D plotting is supported for now.")


    plt.tight_layout()
    plt.show()



def plot_solution_2x2(A, b):
    dim = A.shape[1]

    if dim == 2:
        # ==================================================
        # SOLVE THE SYSTEM
        # ==================================================

        try:
            x = np.linalg.solve(A, b)

        except np.linalg.LinAlgError:
            print("No unique solution exists.")
            return

        print("Solution:")
        print(x)

        # ==================================================
        # FIGURE: SIDE-BY-SIDE SOLUTION PLOTS
        # ==================================================

        fig, (ax1, ax2) = plt.subplots(
            1, 2,
            figsize=(12, 6)
        )

        plt.subplots_adjust(
            wspace=0.35,
            bottom=0.22
        )

        # Common axis limits
        limit = max(
            np.max(np.abs(A)),
            np.max(np.abs(b)),
            np.max(np.abs(x))
        ) * 1.5

        # ==================================================
        # LEFT: INTERSECTION OF ROWS
        # ==================================================

        ax1.set_xlim(-limit, limit)
        ax1.set_ylim(-limit, limit)

        ax1.axhline(0, color="black", linewidth=0.5)
        ax1.axvline(0, color="black", linewidth=0.5)

        ax1.set_aspect("equal")
        ax1.grid()

        ax1.set_title("Intersection of Rows")
        ax1.set_xlabel("x₁")
        ax1.set_ylabel("x₂")

        x_vals = np.linspace(-limit, limit, 400)
        colors = ["red", "blue"]

        # Plot equations
        for i in range(2):
            a1, a2 = A[i]
            rhs = b[i]
            color = colors[i]

            if a2 != 0:
                y_vals = (rhs - a1 * x_vals) / a2

                # Dashed extended line
                ax1.plot(
                    x_vals,
                    y_vals,
                    color=color,
                    linestyle="--",
                    linewidth=1
                )

                # Solid visible portion
                mask = (
                    (y_vals >= -limit) &
                    (y_vals <= limit)
                )

                ax1.plot(
                    x_vals[mask],
                    y_vals[mask],
                    color=color,
                    linewidth=2,
                    label=f"Equation {i+1}"
                )

            elif a1 != 0:
                x_const = rhs / a1

                ax1.axvline(
                    x_const,
                    color=color,
                    linestyle="--",
                    linewidth=1
                )

                ax1.axvline(
                    x_const,
                    color=color,
                    linewidth=2,
                    label=f"Equation {i+1}"
                )

        # Solution point
        ax1.scatter(
            x[0],
            x[1],
            color="purple",
            s=100,
            zorder=5,
            label="Solution"
        )

        ax1.text(
            x[0],
            x[1],
            f"  ({x[0]:.2f}, {x[1]:.2f})",
            color="purple",
            fontsize=11,
            ha="left",
            va="bottom"
        )

        ax1.legend()

        # ==================================================
        # RIGHT: INTERACTIVE COLUMN COMBINATION
        # ==================================================

        c1 = A[:, 0]
        c2 = A[:, 1]

        ax2.set_xlim(-limit, limit)
        ax2.set_ylim(-limit, limit)

        ax2.axhline(0, color="black", linewidth=0.5)
        ax2.axvline(0, color="black", linewidth=0.5)

        ax2.set_aspect("equal")
        ax2.grid()

        ax2.set_title(
            "Combination of Columns"
        )
        ax2.set_xlabel("x")
        ax2.set_ylabel("y")

        # Target vector b
        ax2.quiver(
            0, 0,
            b[0], b[1],
            angles="xy",
            scale_units="xy",
            scale=1,
            color="green",
            label="Target b"
        )

        # Column vectors
        ax2.quiver(
            0, 0,
            c1[0], c1[1],
            angles="xy",
            scale_units="xy",
            scale=1,
            color="red",
            label="Column 1"
        )

        ax2.quiver(
            0, 0,
            c2[0], c2[1],
            angles="xy",
            scale_units="xy",
            scale=1,
            color="blue",
            label="Column 2"
        )

        # Initial coefficients
        coeff1 = 0
        coeff2 = 0

        result = coeff1 * c1 + coeff2 * c2

        result_arrow = ax2.quiver(
            0, 0,
            result[0], result[1],
            angles="xy",
            scale_units="xy",
            scale=1,
            color="purple",
            label="Combination"
        )

        result_text = ax2.text(
            0.02, 0.95,
            "",
            transform=ax2.transAxes,
            color="purple",
            fontsize=11,
            verticalalignment="top"
        )

        ax2.legend()

        # ==================================================
        # SLIDERS AT THE BOTTOM
        # ==================================================

        ax_slider1 = plt.axes([0.15, 0.09, 0.7, 0.025])
        ax_slider2 = plt.axes([0.15, 0.04, 0.7, 0.025])

        slider1 = Slider(
            ax_slider1,
            "x₁",
            -5,
            5,
            valinit=0,
            valstep=0.01
        )

        slider2 = Slider(
            ax_slider2,
            "x₂",
            -5,
            5,
            valinit=0,
            valstep=0.01
        )

        def update(val):
            x1 = slider1.val
            x2 = slider2.val

            result = x1 * c1 + x2 * c2

            result_arrow.set_offsets(
                np.array([[0, 0]])
            )

            result_arrow.set_UVC(
                result[0],
                result[1]
            )

            result_text.set_text(
                f"x₁ = {x1:.2f}, x₂ = {x2:.2f}\n"
                f"Combination = ({result[0]:.2f}, "
                f"{result[1]:.2f})\n"
                f"Target b = ({b[0]:.2f}, {b[1]:.2f})"
            )

            fig.canvas.draw_idle()

        slider1.on_changed(update)
        slider2.on_changed(update)

        update(None)
        plt.show()

    else:
        print("Only 2D plotting is supported for now.")




















# Only execute when running this file directly
if __name__ == "__main__":
    pass