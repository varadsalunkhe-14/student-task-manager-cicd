// Toggle a task's completed status without a full page reload.
async function toggleTask(taskId) {
  try {
    const response = await fetch(`/toggle/${taskId}`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error("Failed to update task");
    }

    const data = await response.json();
    const taskEl = document.getElementById(`task-${taskId}`);

    if (data.is_completed) {
      taskEl.classList.add("completed");
    } else {
      taskEl.classList.remove("completed");
    }
  } catch (err) {
    console.error(err);
    alert("Something went wrong updating the task. Please try again.");
  }
}
