// Drag and Drop Functionality
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const outputZone = document.getElementById('output-zone');
const processButton = document.getElementById('process-button');
const outputMessage = document.getElementById('output-message');
const outputImage = document.getElementById('output-image');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    handleFiles(files);
});

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
    const files = fileInput.files;
    handleFiles(files);
});

function handleFiles(files) {
    const file = files[0];
    if (file) {
        // Display the image
        const reader = new FileReader();
        reader.onload = function (e) {
            outputImage.src = e.target.result;
            outputImage.style.display = 'block'; // Show the image
        };
        reader.readAsDataURL(file);

        // Store the file for processing when the button is clicked
        dropZone.file = file;
    }
}

// Button click event to process the image
processButton.addEventListener('click', () => {
    const file = dropZone.file;
    if (file) {
        // Send the file to the backend for processing
        processImage(file);
    } else {
        alert("Please upload an image first.");
    }
});

function processImage(file) {
    const formData = new FormData();
    formData.append('files', file);  // Key should match the FastAPI parameter name

    outputMessage.textContent = "Processing...";
    outputImage.style.display = 'block'; // Ensure image is shown

    fetch('http://localhost:8000/predict/', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            // Handle the response from the backend
            if (data.predictions.length > 0) {
                const result = data.predictions[0].class_name;
                outputMessage.textContent = result;
            } else {
                outputMessage.textContent = "No prediction available.";
            }
        })
        .catch(error => {
            // Handle any errors that occurred during the request
            console.error('Error:', error);
            outputMessage.textContent = "An error occurred during processing.";
        });
}
