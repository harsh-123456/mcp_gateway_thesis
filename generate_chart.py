import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set academic plotting style for LaTeX readiness
plt.style.use('seaborn-v0_8-paper')
sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)

def generate_chart():
    print("📊 Loading benchmark dataset...")
    try:
        df = pd.read_csv("thesis_benchmark_results.csv")
    except FileNotFoundError:
        print("❌ ERROR: 'thesis_benchmark_results.csv' not found.")
        return

    # Calculate the mean latency for each scenario
    summary = df.groupby("Scenario")["Latency (ms)"].mean().reset_index()

    # Initialize the figure with proper dimensions for a thesis page
    plt.figure(figsize=(10, 6))
    
    # Define a distinct color palette
    colors = ['#4C72B0', '#55A868', '#C44E52', '#8172B3']
    
    # Generate the bar plot
    ax = sns.barplot(
        x="Scenario", 
        y="Latency (ms)", 
        data=summary, 
        palette=colors,
        hue="Scenario",
        legend=False
    )

    # Format the chart titles and labels
    plt.title("System Latency Comparison: Baseline vs. Policy-Aware Gateway", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Average Latency (ms)", fontsize=12, fontweight='bold')
    plt.xlabel("Execution Scenario", fontsize=12, fontweight='bold')
    
    # Clean up the x-axis labels so they fit nicely
    scenarios_clean = [
        "Direct Baseline\n(Control)", 
        "Gateway\nAllowed Request", 
        "Gateway\nBlocked File", 
        "Gateway\nBlocked Role"
    ]
    ax.set_xticklabels(scenarios_clean)
    
    # Add the exact millisecond values on top of each bar
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1f} ms", 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha='center', va='center', 
                    xytext=(0, 10), 
                    textcoords='offset points',
                    fontsize=11, fontweight='bold', color='#333333')

    plt.tight_layout()
    
    # Save as a high-resolution PNG for Overleaf
    filename = "fig_latency_comparison.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Success! Publication-quality chart saved as '{filename}'")

if __name__ == "__main__":
    generate_chart()