import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
class Visualizer:
    def __init__(self):
        pass

    def plot_yes_price(self, df, title="Yes Price Over Time"):
        df["created_time"] = pd.to_datetime(df["created_time"], errors='coerce')
        df = df.sort_values("created_time")
        
        # Filter out any missing or invalid entries
        df = df[df["yes_price"].notnull() & df["created_time"].notnull()]

        # Plot
        plt.figure(figsize=(10, 5))
        plt.plot(df["created_time"], df["yes_price"], marker='o', linestyle='-', alpha=0.7)
        plt.title(title)
        plt.xlabel("Time")
        plt.ylabel("Yes Price")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_yes_price(self, df, title="Yes Price Over Time"):
        df["created_time"] = pd.to_datetime(df["created_time"], errors='coerce')
        df = df.sort_values("created_time")
        
        # Filter out any missing or invalid entries
        df = df[df["yes_price"].notnull() & df["created_time"].notnull()]

        # Plot
        plt.figure(figsize=(10, 5))
        plt.plot(df["created_time"], df["yes_price"], marker='o', linestyle='-', alpha=0.7)
        plt.title(title)
        plt.xlabel("Time")
        plt.ylabel("Yes Price")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    import pandas as pd

    def plot_market_percentages(self, df, yes_label="YES", no_label="NO", title="Market Probability Over Time"):
        # Ensure datetime format
        df["created_time"] = pd.to_datetime(df["created_time"], errors="coerce")
        df = df.sort_values("created_time")

        # Convert price to percentage
        df["yes_pct"] = df["yes_price"]
        df["no_pct"] = 100 - df["yes_pct"]

        # Plot
        plt.figure(figsize=(10, 5))
        plt.plot(df["created_time"], df["yes_pct"], label=yes_label, color="blue", linewidth=2)
        plt.plot(df["created_time"], df["no_pct"], label=no_label, color="gray", linewidth=2, linestyle="--")

        # Optional: horizontal reference lines
        for level in [30, 50, 70]:
            plt.axhline(level, color='lightgray', linestyle=':', linewidth=1)

        plt.title(title)
        plt.ylabel("Implied Probability (%)")
        plt.xlabel("Time")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
