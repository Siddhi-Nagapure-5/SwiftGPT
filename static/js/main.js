document.addEventListener('DOMContentLoaded', function() {
    // Add hover effect to all interactive elements
    const interactiveElements = document.querySelectorAll('.btn, .card, .expanding-panel, .nav-link');
    
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.transition = 'all 0.3s ease';
        });
        
        element.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
    
    // Flash messages auto-dismiss
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(message => {
                message.style.opacity = '0';
                message.style.transition = 'opacity 0.5s ease';
                
                setTimeout(() => {
                    message.remove();
                }, 500);
            });
        }, 5000);
    }
    
    // File upload previews
    const fileInputs = document.querySelectorAll('.file-upload-input');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'No file selected';
            const fileNameDisplay = this.parentElement.querySelector('.file-name');
            
            if (fileNameDisplay) {
                fileNameDisplay.textContent = fileName;
            } else {
                const nameSpan = document.createElement('div');
                nameSpan.className = 'file-name';
                nameSpan.textContent = fileName;
                this.parentElement.appendChild(nameSpan);
            }
            
            // Update label
            const label = this.parentElement.querySelector('.file-upload-label');
            if (label) {
                label.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg> <span>File selected</span>';
            }
        });
    });
    
    // Custom select styling
    const selects = document.querySelectorAll('select.form-control');
    
    selects.forEach(select => {
        // Add event listener to maintain focus styling
        select.addEventListener('focus', function() {
            this.parentElement.classList.add('select-focused');
        });
        
        select.addEventListener('blur', function() {
            this.parentElement.classList.remove('select-focused');
        });
    });
    
    // Tag input functionality
    const tagInputs = document.querySelectorAll('.tags-input');
    
    tagInputs.forEach(container => {
        const input = container.querySelector('input');
        const hiddenInput = document.querySelector(`#${container.dataset.for}`);
        
        if (!input || !hiddenInput) return;
        
        // Initialize with any existing tags
        if (hiddenInput.value) {
            const initialTags = hiddenInput.value.split(',');
            initialTags.forEach(tag => {
                if (tag.trim()) {
                    addTag(tag.trim(), container, hiddenInput);
                }
            });
        }
        
        // Add tag on Enter or comma
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                
                const tag = this.value.trim();
                if (tag) {
                    addTag(tag, container, hiddenInput);
                    this.value = '';
                }
            }
        });
        
        // Add tag when input loses focus
        input.addEventListener('blur', function() {
            const tag = this.value.trim();
            if (tag) {
                addTag(tag, container, hiddenInput);
                this.value = '';
            }
        });
    });
    
    // Function to add a tag to a container
    function addTag(text, container, hiddenInput) {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.innerHTML = `${text} <span class="tag-close">&times;</span>`;
        
        // Insert before the input
        const input = container.querySelector('input');
        container.insertBefore(tag, input);
        
        // Update hidden input with all tags
        updateHiddenInput(container, hiddenInput);
        
        // Add click event to remove tag
        const closeBtn = tag.querySelector('.tag-close');
        closeBtn.addEventListener('click', function() {
            container.removeChild(tag);
            updateHiddenInput(container, hiddenInput);
        });
    }
    
    // Function to update the hidden input with all current tags
    function updateHiddenInput(container, hiddenInput) {
        const tags = Array.from(container.querySelectorAll('.tag'))
            .map(tag => tag.textContent.trim().replace('×', '').trim());
        hiddenInput.value = tags.join(',');
    }
    
    // Responsive navigation
    const menuToggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('.nav');
    
    if (menuToggle && nav) {
        menuToggle.addEventListener('click', function() {
            nav.classList.toggle('nav-open');
            this.classList.toggle('active');
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('form.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
            
            // Highlight invalid fields
            const invalidFields = form.querySelectorAll(':invalid');
            invalidFields.forEach(field => {
                field.classList.add('is-invalid');
                
                // Add error message if not present
                const parent = field.parentElement;
                if (!parent.querySelector('.form-error')) {
                    const errorMsg = document.createElement('div');
                    errorMsg.className = 'form-error';
                    errorMsg.textContent = field.validationMessage || 'This field is required';
                    parent.appendChild(errorMsg);
                }
            });
        });
        
        // Live validation on input
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    
                    // Remove error message
                    const errorMsg = this.parentElement.querySelector('.form-error');
                    if (errorMsg) {
                        errorMsg.remove();
                    }
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
        });
    });
});
