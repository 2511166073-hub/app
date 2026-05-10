// RSD Scoring - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // Confirm before submitting evidence
    const evidenceForms = document.querySelectorAll('form[action*="submit-evidence"]');
    evidenceForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const description = document.querySelector('#description')?.value;
            if (!description || description.length < 10) {
                e.preventDefault();
                alert('Vui lòng mô tả chi tiết minh chứng (ít nhất 10 ký tự)');
            }
        });
    });

    // Dynamic points selection based on evidence type
    const evidenceTypeSelect = document.querySelector('#evidence_type');
    const pointsSelect = document.querySelector('select[name="points"]');
    
    if (evidenceTypeSelect && pointsSelect) {
        evidenceTypeSelect.addEventListener('change', function() {
            const type = this.value;
            pointsSelect.innerHTML = '';
            
            const options = {
                'absence': [{value: '0', text: '0 (duyệt vắng có phép)'}],
                'task': [{value: '0', text: '0'}, {value: '1', text: '+1 (hoàn thành sớm)'}],
                'idea': [{value: '2', text: '+2 (ý tưởng chất lượng)'}],
                'initiative': [{value: '1', text: '+1 (chủ động)'}],
                'agenda': [
                    {value: '0', text: '0'},
                    {value: '-1', text: '-1 (nộp trễ)'},
                    {value: '-2', text: '-2 (không nộp)'}
                ],
                'minutes': [
                    {value: '0', text: '0'},
                    {value: '-1', text: '-1 (nộp trễ)'},
                    {value: '-2', text: '-2 (không nộp)'}
                ]
            };
            
            (options[type] || []).forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.text;
                pointsSelect.appendChild(option);
            });
        });
    }

    // Meeting type deadline info
    const meetingTypeSelect = document.querySelector('#meeting_type');
    if (meetingTypeSelect) {
        meetingTypeSelect.addEventListener('change', function() {
            const type = this.value;
            const infoBox = document.querySelector('.info-box');
            if (infoBox) {
                if (type === 'ban') {
                    infoBox.innerHTML = '<h4>📌 Lưu ý:</h4><ul><li>Vắng có phép: 0 điểm</li><li>Vắng không phép: -1 điểm</li><li>Vắng >2 buổi liên tiếp: Cảnh báo</li></ul>';
                } else {
                    infoBox.innerHTML = '<h4>📌 Lưu ý:</h4><ul><li>Vắng có phép: -1 điểm</li><li>Vắng không phép: -2 điểm</li><li>Vắng >3 buổi liên tiếp: Cảnh báo</li></ul>';
                }
            }
        });
    }

    // Table row highlight on hover
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        row.addEventListener('mouseleave', function() {
            if (!this.classList.contains('top-rank')) {
                this.style.backgroundColor = '';
            }
        });
    });

    console.log('RSD Scoring System loaded successfully!');
});
