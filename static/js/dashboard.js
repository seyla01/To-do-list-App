// static/js/dashboard.js
const ctx = document.getElementById("activityChart");
new Chart(ctx, {
  type: "line",
  data: {
    labels: weekLabels,
    datasets: [{
      label: "Tasks Completed",
      data: weekData,
      borderColor: "#6366F1",
      backgroundColor: "rgba(99,102,241,0.2)",
      borderWidth: 2,
      fill: true,
      tension: 0.4
    }]
  },
  options: {
    responsive: true,
    scales: { y: { beginAtZero: true } },
    plugins: { legend: { display: false } }
  }
});

