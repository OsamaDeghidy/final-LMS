document.addEventListener('DOMContentLoaded', function() {
  // Find all image upload inputs
  const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
  
  imageInputs.forEach(input => {
    input.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (!file) return;
      
      const reader = new FileReader();
      reader.onload = function(event) {
        // Find the parent container (usually a div)
        const container = e.target.closest('.card');
        if (!container) return;
        
        // Store the original input element
        const originalInput = e.target;
        
        // Create a preview element
        const previewHTML = `
          <div class="text-center preview-container">
            <img src="${event.target.result}" class="img-thumbnail mb-2" style="max-height: 200px;">
            <p class="small text-muted">${file.name}</p>
            <button type="button" class="btn btn-sm btn-outline-danger remove-preview">
              تغيير الصورة
            </button>
          </div>
        `;
        
        // Remove any existing preview
        const existingPreview = container.querySelector('.preview-container');
        if (existingPreview) {
          existingPreview.remove();
        }
        
        // Hide the upload icon and text
        const uploadElements = container.querySelectorAll('.fa-cloud-upload-alt, .text-muted');
        uploadElements.forEach(el => {
          el.style.display = 'none';
        });
        
        // Append the preview to the container
        container.insertAdjacentHTML('beforeend', previewHTML);
        
        // Add event listener to the remove button
        container.querySelector('.remove-preview').addEventListener('click', function() {
          // Remove the preview
          this.closest('.preview-container').remove();
          
          // Show the upload icon and text again
          uploadElements.forEach(el => {
            el.style.display = '';
          });
          
          // Clear the file input
          originalInput.value = '';
        });
      };
      
      reader.readAsDataURL(file);
    });
  });
});
