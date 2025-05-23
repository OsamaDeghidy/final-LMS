document.addEventListener('DOMContentLoaded', function() {
  // Find the image upload field
  const imageInput = document.getElementById('image_course');
  if (!imageInput) return;

  // Remove any existing event listeners by cloning and replacing the element
  const newImageInput = imageInput.cloneNode(true);
  imageInput.parentNode.replaceChild(newImageInput, imageInput);
  
  // Add our new event listener
  newImageInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(event) {
      // Find the parent container
      const container = e.target.closest('.card');
      if (!container) return;
      
      // Remove any existing preview
      const existingPreview = container.querySelector('.preview-container');
      if (existingPreview) {
        existingPreview.remove();
      }
      
      // Hide the upload icons and text
      const uploadIcons = container.querySelectorAll('.fa-cloud-upload-alt, h5.text-muted');
      uploadIcons.forEach(el => {
        el.style.display = 'none';
      });
      
      // Create a preview element
      const previewDiv = document.createElement('div');
      previewDiv.className = 'preview-container text-center mt-3';
      previewDiv.innerHTML = `
        <img src="${event.target.result}" class="img-thumbnail mb-2" style="max-height: 200px;">
        <p class="small text-muted">${file.name}</p>
      `;
      
      // Add the preview to the container
      container.appendChild(previewDiv);
    };
    
    reader.readAsDataURL(file);
  });
});
