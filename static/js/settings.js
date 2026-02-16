const displayName = document.getElementById('display-name');
const saveBtn = document.getElementById('save-btn');

// Show the save button only when they start typing
displayName.addEventListener('input', () => {
    saveBtn.style.display = 'inline-block';
});

saveBtn.addEventListener('click', async () => {
    const newName = displayName.innerText.trim();
    
    // Create form data to match your FastAPI Form(...) parameters
    const formData = new FormData();
    formData.append('new_display_name', newName);

    try {
        const response = await fetch('/settings/edit/display_name', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            saveBtn.style.display = 'none';
            alert('Profile updated!');
            location.reload(); // Reload to show the updated name and reset the original data attribute
        } else {
            alert('Failed to update. Try again.');
            displayName.innerText = displayName.getAttribute('data-original');
        }
    } catch (error) {
        console.error('Error:', error);
    }
});

async function deleteIcon(iconId) {
    if (!confirm("Are you sure you want to delete this icon? This cannot be undone.")) {
        location.reload();
        return;
    }

    try {
        const response = await fetch(`/icon/${iconId}/delete`, {
            method: 'POST'
        });

        if (response.ok) {
            // Remove the element from the DOM immediately
            const element = document.getElementById(`icon-row-${iconId}`);
            element.style.opacity = '0';
            setTimeout(() => element.remove(), 300);
        } else {
            alert("Error: Could not delete icon. You may not have permission.");
        }
    } catch (error) {
        console.error("Delete error:", error);
    }
}