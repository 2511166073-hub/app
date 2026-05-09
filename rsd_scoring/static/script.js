// Toggle evidence type fields
document.addEventListener('DOMContentLoaded', function() {
    const evidenceType = document.getElementById('evidence_type');
    const taskField = document.getElementById('task_id').parentElement;
    const meetingField = document.getElementById('meeting_id').parentElement;
    
    if (evidenceType) {
        evidenceType.addEventListener('change', function() {
            if (this.value === 'task') {
                taskField.style.display = 'block';
                meetingField.style.display = 'none';
            } else {
                taskField.style.display = 'none';
                meetingField.style.display = 'block';
            }
        });
        
        // Trigger initial state
        evidenceType.dispatchEvent(new Event('change'));
    }
});

// Confirm delete actions
function confirmDelete(message) {
    return confirm(message || 'Bạn có chắc chắn muốn xóa?');
}
