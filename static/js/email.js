document.addEventListener('DOMContentLoaded', function() {
    // Handle the tag filtering for contacts
    const tagFilter = document.getElementById('tag-filter');
    const contactList = document.getElementById('contact-list');
    const tagsInput = document.getElementById('tags-input');
    
    if (tagFilter && contactList) {
        tagFilter.addEventListener('click', function() {
            const tags = tagsInput.value.trim();
            
            if (!tags) {
                alert('Please enter at least one tag to filter contacts.');
                return;
            }
            
            // Show loading state
            contactList.innerHTML = '<div class="text-center p-3"><div class="spinner-border text-primary" role="status"></div><div class="mt-2">Loading contacts...</div></div>';
            
            // Send AJAX request to get filtered contacts
            const formData = new FormData();
            formData.append('tags', tags);
            
            fetch('/get_filtered_contacts', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.contacts && data.contacts.length > 0) {
                    renderContacts(data.contacts);
                } else {
                    contactList.innerHTML = '<div class="text-center p-3">No contacts found with the specified tags.</div>';
                }
            })
            .catch(error => {
                console.error('Error fetching contacts:', error);
                contactList.innerHTML = '<div class="text-center p-3 text-danger">Error loading contacts. Please try again.</div>';
            });
        });
    }
    
    // Function to render the contacts list
    function renderContacts(contacts) {
        contactList.innerHTML = '';
        
        contacts.forEach(contact => {
            const contactItem = document.createElement('div');
            contactItem.className = 'contact-item';
            
            // Format the tags as badges
            const tagHtml = contact.tags ? contact.tags.split(',').map(tag => 
                `<span class="contact-tag">${tag.trim()}</span>`
            ).join('') : '';
            
            contactItem.innerHTML = `
                <div class="form-check">
                    <input type="checkbox" class="form-check-input" id="contact-${contact.id}" name="contact_ids" value="${contact.id}">
                    <label class="form-check-label" for="contact-${contact.id}"></label>
                </div>
                <div class="contact-info">
                    <div class="contact-name">${contact.name}</div>
                    <div class="contact-email">${contact.email}</div>
                    <div class="contact-tags">${tagHtml}</div>
                </div>
            `;
            
            contactList.appendChild(contactItem);
        });
        
        // Add select all functionality
        const selectAllContainer = document.createElement('div');
        selectAllContainer.className = 'select-all-container p-2 border-bottom';
        selectAllContainer.innerHTML = `
            <div class="form-check">
                <input type="checkbox" class="form-check-input" id="select-all">
                <label class="form-check-label" for="select-all">Select All (${contacts.length} contacts)</label>
            </div>
        `;
        contactList.insertBefore(selectAllContainer, contactList.firstChild);
        
        // Add event listener for select all
        const selectAll = document.getElementById('select-all');
        selectAll.addEventListener('change', function() {
            const checkboxes = contactList.querySelectorAll('input[name="contact_ids"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAll.checked;
            });
        });
    }
    
    // Show/hide schedule options
    const scheduleCheckbox = document.getElementById('schedule-checkbox');
    const scheduleOptions = document.getElementById('schedule-options');
    
    if (scheduleCheckbox && scheduleOptions) {
        scheduleCheckbox.addEventListener('change', function() {
            if (this.checked) {
                scheduleOptions.style.display = 'block';
            } else {
                scheduleOptions.style.display = 'none';
            }
        });
    }
    
    // Initialize date/time inputs with current datetime
    const scheduleDateInput = document.getElementById('schedule-date');
    const scheduleTimeInput = document.getElementById('schedule-time');
    
    if (scheduleDateInput && scheduleTimeInput) {
        const now = new Date();
        
        // Format date as YYYY-MM-DD
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        scheduleDateInput.value = `${year}-${month}-${day}`;
        
        // Format time as HH:MM
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        scheduleTimeInput.value = `${hours}:${minutes}`;
    }
    
    // Handle contact selection count and button enabling
    function updateSelectedCount() {
        const selectedCheckboxes = document.querySelectorAll('input[name="contact_ids"]:checked');
        const selectedCount = selectedCheckboxes.length;
        const countDisplay = document.getElementById('selected-count');
        const submitBtn = document.getElementById('send-email-btn');
        const scheduleBtn = document.getElementById('schedule-email-btn');
        
        if (countDisplay) {
            countDisplay.textContent = selectedCount.toString();
        }
        
        if (submitBtn) {
            submitBtn.disabled = selectedCount === 0;
        }
        
        if (scheduleBtn) {
            scheduleBtn.disabled = selectedCount === 0;
        }
    }
    
    // Add event delegation for contact checkboxes
    if (contactList) {
        contactList.addEventListener('change', function(e) {
            if (e.target.name === 'contact_ids') {
                updateSelectedCount();
            }
        });
    }
    
    // CSV file validation
    const csvFileInput = document.getElementById('contact-file');
    const csvSubmitBtn = document.getElementById('upload-contacts-btn');
    
    if (csvFileInput && csvSubmitBtn) {
        csvFileInput.addEventListener('change', function() {
            const file = this.files[0];
            
            if (file) {
                // Check file extension
                const fileExt = file.name.split('.').pop().toLowerCase();
                if (fileExt !== 'csv') {
                    alert('Please select a CSV file.');
                    this.value = '';
                    csvSubmitBtn.disabled = true;
                    return;
                }
                
                csvSubmitBtn.disabled = false;
            } else {
                csvSubmitBtn.disabled = true;
            }
        });
    }
    
    // Allow tags to be entered and create visual chips
    const tagInput = document.getElementById('tags-input');
    const tagContainer = document.getElementById('tag-container');
    
    if (tagInput && tagContainer) {
        tagInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                
                const tag = this.value.trim().replace(',', '');
                if (tag) {
                    addTagChip(tag);
                    this.value = '';
                }
            }
        });
        
        function addTagChip(tag) {
            const tagChip = document.createElement('span');
            tagChip.className = 'tag';
            tagChip.innerHTML = `${tag} <span class="tag-close">&times;</span>`;
            tagContainer.appendChild(tagChip);
            
            // Add click event to remove tag
            const closeBtn = tagChip.querySelector('.tag-close');
            closeBtn.addEventListener('click', function() {
                tagContainer.removeChild(tagChip);
                updateTagsInput();
            });
            
            updateTagsInput();
        }
        
        function updateTagsInput() {
            const tags = Array.from(tagContainer.querySelectorAll('.tag'))
                .map(tag => tag.textContent.trim().replace('×', '').trim());
            tagInput.value = tags.join(',');
        }
    }
    
    // Preview email before sending
    const previewBtn = document.getElementById('preview-email-btn');
    const emailSubject = document.getElementById('email-subject');
    const emailBody = document.getElementById('email-body');
    const previewContainer = document.getElementById('email-preview-container');
    
    if (previewBtn && emailSubject && emailBody && previewContainer) {
        previewBtn.addEventListener('click', function() {
            previewContainer.innerHTML = `
                <div class="email-preview">
                    <div class="email-preview-header">
                        <div class="email-subject">${emailSubject.textContent}</div>
                    </div>
                    <div class="email-preview-body">${emailBody.textContent.replace(/\n/g, '<br>')}</div>
                </div>
            `;
            
            previewContainer.style.display = 'block';
            previewContainer.scrollIntoView({ behavior: 'smooth' });
        });
    }
});
