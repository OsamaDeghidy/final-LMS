document.addEventListener('DOMContentLoaded', function() {
  // Find the image upload field
  const imageInput = document.getElementById('image_course');
  if (!imageInput) return;

  // Override any existing event listeners for the image upload
  const originalAddEventListener = EventTarget.prototype.addEventListener;
  EventTarget.prototype.addEventListener = function(type, listener, options) {
    // Only override 'change' event for the image_course element
    if (this.id === 'image_course' && type === 'change') {
      // Don't add other change listeners to this element
      return;
    }
    // For all other elements, proceed normally
    return originalAddEventListener.call(this, type, listener, options);
  };

  // Add our own event listener for the image upload
  setTimeout(function() {
    const imageInput = document.getElementById('image_course');
    if (!imageInput) return;
    
    imageInput.addEventListener = originalAddEventListener;
    imageInput.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (!file) return;
      
      const reader = new FileReader();
      reader.onload = function(event) {
        // Find the parent container
        const container = e.target.closest('.card');
        if (!container) return;
        
        // Create a preview element (but don't replace the input)
        const previewDiv = document.createElement('div');
        previewDiv.className = 'preview-container text-center mt-3';
        previewDiv.innerHTML = `
          <img src="${event.target.result}" class="img-thumbnail mb-2" style="max-height: 200px;">
          <p class="small text-muted">${file.name}</p>
        `;
        
        // Hide the upload icons and text
        const uploadIcons = container.querySelectorAll('.fa-cloud-upload-alt, h5.text-muted');
        uploadIcons.forEach(el => {
          if (el) el.style.display = 'none';
        });
        
        // Remove any existing preview
        const existingPreview = container.querySelector('.preview-container');
        if (existingPreview) {
          existingPreview.remove();
        }
        
        // Append the preview to the container
        container.appendChild(previewDiv);
      };
      
      reader.readAsDataURL(file);
    });
  }, 500); // Wait for other scripts to load
});
