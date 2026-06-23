// FilePond Upload Module
let documentPond;

function initializeFilePond() {
    // Check if FilePond is available
    if (typeof FilePond === 'undefined') {
        console.error('FilePond not available');
        setupFallbackUpload();
        return;
    }

    // Register plugins if available
    if (window.FilePondPluginFileValidateType) FilePond.registerPlugin(FilePondPluginFileValidateType);
    if (window.FilePondPluginFileValidateSize) FilePond.registerPlugin(FilePondPluginFileValidateSize);
    if (window.FilePondPluginImagePreview) FilePond.registerPlugin(FilePondPluginImagePreview);
    if (window.FilePondPluginFilePoster) FilePond.registerPlugin(FilePondPluginFilePoster);

    const documentInput = document.querySelector('#document-filepond');
    if (!documentInput) {
        console.error('FilePond input element not found');
        return;
    }

    const acceptedFileTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'application/epub+zip',
        'application/x-mobipocket-ebook',
        '.pdf', '.doc', '.docx', '.txt', '.epub', '.mobi'
    ];

    // Initialize FilePond
    documentPond = FilePond.create(documentInput, {
        allowMultiple: false,
        instantUpload: false,
        allowRevert: true,
        acceptedFileTypes: acceptedFileTypes,
        fileValidateTypeDetectType: (source, type) => new Promise((resolve) => {
            const extension = source.name.split('.').pop().toLowerCase();

            if (!type || type === 'application/octet-stream') {
                switch (extension) {
                    case 'pdf': resolve('application/pdf'); break;
                    case 'doc': resolve('application/msword'); break;
                    case 'docx': resolve('application/vnd.openxmlformats-officedocument.wordprocessingml.document'); break;
                    case 'txt': resolve('text/plain'); break;
                    case 'epub': resolve('application/epub+zip'); break;
                    case 'mobi': resolve('application/x-mobipocket-ebook'); break;
                    default: resolve(type);
                }
            } else {
                resolve(type);
            }
        }),
        className: 'filepond-enhanced',
        labelIdle: '<span class="filepond-icon"><i class="bi bi-file-earmark-arrow-up"></i></span><br>Drag your document here<br> or <span class="filepond--label-action">Browse</span>',
        labelFileTypeNotAllowed: 'Invalid file type. Check the list of allowed formats.',
        labelMaxFileSize: 'The file is too large',
        maxFileSize: '10MB',
        credits: false
    });

    // Setup FilePond event listeners
    setupFilePondListeners();

    // Setup upload form
    setupUploadForm();
}

function setupFilePondListeners() {
    if (!documentPond) return;

    documentPond.on('addfile', (error, file) => {
        if (error) {
            console.error('Error adding file:', error);
            return;
        }

        updateDocumentTypeSelector(file);
        applyFileTypeClass(file);
    });

    documentPond.on('removefile', () => {
        resetDocumentTypeSelector();
    });
}

function setupUploadForm() {
    // Document type selector clicks
    document.querySelectorAll('.document-type-option').forEach(option => {
        option.addEventListener('click', function () {
            if (!documentPond || documentPond.getFiles().length === 0) {
                //showToast('Please upload a document first', 'warning');
                return;
            }

            // Reset all options
            document.querySelectorAll('.document-type-option').forEach(opt => {
                opt.classList.remove('active');
            });

            // Activate selected option
            this.classList.add('active');

            // Update FilePond colors
            const selectedType = this.getAttribute('data-type');
            updateFilePondColors(selectedType);
        });
    });

    // Upload form submission
    const submitButton = document.getElementById('submitDocumentUpload');
    const form = document.getElementById('documentUploadForm');

    if (submitButton && form) {
        submitButton.addEventListener('click', async function (e) {
            e.preventDefault();

            if (!documentPond || !documentPond.getFiles().length) {
                // showToast('Please select a document', 'warning');
                return;
            }

            await handleDocumentUpload();
        });
    }
}

function setupFallbackUpload() {
    const filepondContainer = document.querySelector('#document-filepond-container');
    if (filepondContainer) {
        filepondContainer.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle-fill"></i>
                FilePond library not available. Using fallback upload.
            </div>
            <input type="file" class="form-control" id="fallback-file-input" name="document" accept=".pdf,.doc,.docx,.txt,.epub,.mobi">
        `;
    }
}

// Document Type Management
function updateDocumentTypeSelector(file) {
    const typeContainer = document.getElementById('type-detection-container');
    const allOptions = document.querySelectorAll('.document-type-option');

    if (!file) {
        resetDocumentTypeSelector();
        return;
    }

    const fileType = file.fileType;
    const extension = file.filename.split('.').pop().toLowerCase();

    let dataType = '';

    if (fileType.includes('pdf') || extension === 'pdf') {
        dataType = 'pdf';
    } else if (fileType.includes('openxmlformats') || extension === 'docx') {
        dataType = 'docx';
    } else if (fileType.includes('msword') || extension === 'doc') {
        dataType = 'doc';
    } else if (fileType.includes('text/plain') || extension === 'txt') {
        dataType = 'txt';
    } else if (fileType.includes('epub') || extension === 'epub') {
        dataType = 'epub';
    } else if (fileType.includes('mobipocket') || extension === 'mobi') {
        dataType = 'mobi';
    } else {
        resetDocumentTypeSelector();
        return;
    }

    // Add detected type class
    typeContainer.classList.add('detected-type-container');
    typeContainer.classList.add(`${dataType}-detected`);

    // Show only the corresponding option
    allOptions.forEach(option => {
        const optionType = option.getAttribute('data-type');
        const column = option.closest('.col-2, .col-12');

        if (optionType === dataType) {
            column.classList.remove('d-none');
            column.classList.remove('col-2');
            column.classList.add('col-12');
            option.classList.add('active', 'single-option');
        } else {
            column.classList.add('d-none');
            option.classList.remove('active', 'single-option');
        }
    });

    // Update description
    const descriptionElement = document.querySelector('.document-type-selector h6');
    if (descriptionElement) {
        const typeIcon = getTypeIcon(dataType);
        descriptionElement.innerHTML = `${typeIcon} Document type detected:`;
        descriptionElement.classList.add('detected-type-text');
    }

    // Update FilePond colors
    updateFilePondColors(dataType);
}

function resetDocumentTypeSelector() {
    const typeContainer = document.getElementById('type-detection-container');
    const allOptions = document.querySelectorAll('.document-type-option');

    // Remove detected type classes
    typeContainer.classList.remove('detected-type-container');
    typeContainer.className = typeContainer.className.replace(/\w+-detected/g, '');

    // Show all options
    allOptions.forEach(option => {
        const column = option.closest('.col-2, .col-12');
        column.classList.remove('d-none');
        column.classList.remove('col-12');
        column.classList.add('col-2');
        option.classList.remove('active', 'single-option');
    });

    // Reset description
    const descriptionElement = document.querySelector('.document-type-selector h6');
    if (descriptionElement) {
        descriptionElement.textContent = 'Accepted formats:';
        descriptionElement.classList.remove('detected-type-text');
    }

    // Reset FilePond colors
    updateFilePondColors(null);
}

function updateFilePondColors(documentType) {
    // Remove all active document type classes
    document.body.classList.remove(
        'document-type-pdf-active',
        'document-type-docx-active',
        'document-type-doc-active',
        'document-type-txt-active',
        'document-type-epub-active',
        'document-type-mobi-active'
    );

    if (documentType) {
        document.body.classList.add(`document-type-${documentType}-active`);
    }
}

function applyFileTypeClass(file) {
    const fileType = file.fileType;
    const extension = file.filename.split('.').pop().toLowerCase();

    let fileTypeClass = '';
    let fileIcon = '';

    if (fileType.includes('pdf') || extension === 'pdf') {
        fileTypeClass = 'file-type-pdf';
        fileIcon = '<i class="bi bi-file-earmark-pdf-fill"></i>';
    } else if (fileType.includes('word') || extension === 'docx') {
        fileTypeClass = 'file-type-word';
        fileIcon = '<i class="bi bi-file-earmark-word-fill"></i>';
    } else if (extension === 'doc') {
        fileTypeClass = 'file-type-doc';
        fileIcon = '<i class="bi bi-file-earmark-word"></i>';
    } else if (fileType.includes('text/plain') || extension === 'txt') {
        fileTypeClass = 'file-type-txt';
        fileIcon = '<i class="bi bi-file-earmark-text-fill"></i>';
    } else if (fileType.includes('epub') || extension === 'epub') {
        fileTypeClass = 'file-type-epub';
        fileIcon = '<i class="bi bi-book-fill"></i>';
    } else if (fileType.includes('mobipocket') || extension === 'mobi') {
        fileTypeClass = 'file-type-mobi';
        fileIcon = '<i class="bi bi-tablet"></i>';
    }

    // Add class to file element
    const fileElement = document.querySelector(`.filepond--item[data-filepond-item-id="${file.id}"]`);
    if (fileElement) {
        fileElement.classList.remove(
            'file-type-pdf', 'file-type-word', 'file-type-doc',
            'file-type-txt', 'file-type-epub', 'file-type-mobi'
        );

        fileElement.classList.add(fileTypeClass);

        // Add preview icon
        const filePreview = document.createElement('div');
        filePreview.className = 'file-preview-icon';
        filePreview.innerHTML = fileIcon;

        const existingIcon = fileElement.querySelector('.file-preview-icon');
        if (existingIcon) {
            existingIcon.remove();
        }

        const fileWrapper = fileElement.querySelector('.filepond--file-wrapper');
        if (fileWrapper) {
            fileWrapper.prepend(filePreview);
        }
    }
}

function getTypeIcon(dataType) {
    const icons = {
        pdf: '<i class="bi bi-file-earmark-pdf-fill text-danger"></i>',
        docx: '<i class="bi bi-file-earmark-word-fill text-primary"></i>',
        doc: '<i class="bi bi-file-earmark-word text-primary"></i>',
        txt: '<i class="bi bi-file-earmark-text-fill text-success"></i>',
        epub: '<i class="bi bi-book-fill text-warning"></i>',
        mobi: '<i class="bi bi-tablet text-danger"></i>'
    };

    return icons[dataType] || '';
}

// Upload Handling
async function handleDocumentUpload() {
    const uploadStatus = document.getElementById('uploadStatus');
    const progressBar = document.getElementById('uploadProgressBar');
    const progressText = document.getElementById('uploadProgressText');
    const statusIcon = document.getElementById('uploadStatusIcon');
    const statusText = document.getElementById('uploadStatusText');
    const documentFilepondContainer = document.getElementById('document-filepond-container');
    const documentTypeContainer = document.getElementById('document-type-container');

    try {
        // Show upload status
        uploadStatus.classList.remove('d-none', 'alert-danger', 'alert-success');
        uploadStatus.classList.add('alert-info');

        // Disable submit button
        documentFilepondContainer.style.display = 'none';
        documentTypeContainer.style.display = 'none';
        const submitButton = document.getElementById('submitDocumentUpload');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Processing...
            `;
        }

        // Initialize progress
        updateUploadProgress(0, 'Preparing document...', 'bi bi-arrow-repeat spin');

        // Prepare form data
        const formData = new FormData();
        const files = documentPond.getFiles();

        if (files.length > 0) {
            formData.append('save_file', files[0].file); // API expects 'save_file'

            const activeType = document.querySelector('.document-type-option.active');
            if (activeType) {
                const documentType = activeType.getAttribute('data-type');
                formData.append('document_type', documentType);
            }

            formData.append('user_id', currentUserData?.id || ''); // Assuming user identity
            if (typeof currentFolderId !== 'undefined' && currentFolderId !== null) {
                formData.append('folder_id', currentFolderId);
            }

            formData.append('upload_timestamp', new Date().toISOString());
            formData.append('filename_original', files[0].filename);
            formData.append('filesize', files[0].fileSize);
        }

        // Simulate upload phases
        await simulateUploadPhases(progressBar, progressText, statusText, statusIcon);

        // Perform actual upload
        await performUpload(formData);

        // Show success
        showUploadSuccess(files[0]);

    } catch (error) {
        documentFilepondContainer.style.display = 'block';
        documentTypeContainer.style.display = 'block';
        console.error('Upload error:', error);
        showUploadError(error.message || 'Error uploading document');
    }
}

async function simulateUploadPhases(progressBar, progressText, statusText, statusIcon) {
    // Phase 1: Security scan
    updateUploadProgress(30, 'Analyzing document security...', 'bi bi-shield-check');
    await delay(1000);

    // Phase 2: Upload
    updateUploadProgress(60, 'Uploading to server...', 'bi bi-cloud-upload');
    await delay(1000);

    // Phase 3: Processing
    updateUploadProgress(90, 'Processing document...', 'bi bi-gear-fill spin');
    await delay(500);
}

async function performUpload(formData) {
    const documentFilepondContainer = document.getElementById('document-filepond-container');
    const documentTypeContainer = document.getElementById('document-type-container');
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = Math.round(90 + (event.loaded / event.total) * 10);
                updateUploadProgress(percentComplete, 'Uploading to server...', 'bi bi-cloud-upload');
            }
        };

        xhr.onload = function () {
            if (xhr.status >= 200 && xhr.status < 300) {
                const result = JSON.parse(xhr.responseText);
                updateUploadProgress(100, 'Upload complete!', 'bi bi-check-circle-fill text-success');
                resolve(result);
                // Reload or navigate
                setTimeout(() => {
                    if (typeof loadFolderContent === 'function') {
                        loadFolderContent(currentFolderId);
                        resetUploadForm();
                        closeModals();
                    } else {
                        window.location.reload();
                    }
                }, 1500);
            } else {
                documentFilepondContainer.style.display = 'block';
                documentTypeContainer.style.display = 'block';
                reject(new Error(`Upload failed (${xhr.status})`));
            }
        };

        xhr.onerror = function () {
            documentFilepondContainer.style.display = 'block';
            documentTypeContainer.style.display = 'block';
            reject(new Error('Network error during upload'));
        };

        xhr.open('POST', '/x_doc/uploadsave', true);
        xhr.send(formData);
    });
}

//function updateUploadProgress(percentage, message, iconClass) {
//    const progressBar = document.getElementById('uploadProgressBar');
//    const progressText = document.getElementById('uploadProgressText');
//    const statusText = document.getElementById('uploadStatusText');
//    const statusIcon = document.getElementById('uploadStatusIcon');
//    const stageText = document.getElementById('uploadStageText');

//    if (progressBar) {
//        progressBar.style.width = `${percentage}%`;
//        progressBar.setAttribute('aria-valuenow', percentage);
//    }

//    if (progressText) progressText.textContent = `${percentage}%`;
//    if (statusText) statusText.textContent = message;
//    if (statusIcon) statusIcon.className = iconClass;
//    if (stageText) stageText.textContent = message;
//}

// Modificar la función updateUploadProgress para incluir estado de error
function updateUploadProgress(percentage, message, iconClass, isError = false) {
    const progressBar = document.getElementById('uploadProgressBar');
    const progressText = document.getElementById('uploadProgressText');
    const statusText = document.getElementById('uploadStatusText');
    const statusIcon = document.getElementById('uploadStatusIcon');
    const stageText = document.getElementById('uploadStageText');

    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', percentage);

        // Remover clases anteriores
        progressBar.classList.remove('uploading', 'error');

        if (isError) {
            // Estado de error
            progressBar.classList.add('error');
        } else if (percentage > 0 && percentage < 100) {
            // Estado normal de carga
            progressBar.classList.add('uploading');
        }
    }

    if (progressText) progressText.textContent = `${percentage}%`;
    if (statusText) statusText.textContent = message;
    if (statusIcon) statusIcon.className = iconClass;
    if (stageText) stageText.textContent = message;
}


function showUploadSuccess(file) {
    const uploadStatus = document.getElementById('uploadStatus');
    uploadStatus.classList.remove('alert-info');
    uploadStatus.classList.add('alert-success');

    const statusText = document.getElementById('uploadStatusText');
    if (statusText) {
        statusText.textContent = `${file.filename} uploaded successfully!`;
    }

    showToast('Document uploaded successfully!', 'success');

    // Reset form after delay
    setTimeout(() => {
        resetUploadForm();
    }, 2000);
}


// Nueva función específica para mostrar error
function showUploadError(message) {
    const uploadStatus = document.getElementById('uploadStatus');
    const statusText = document.getElementById('uploadStatusText');
    const statusIcon = document.getElementById('uploadStatusIcon');
    const progressBar = document.getElementById('uploadProgressBar');

    // Cambiar a estado de error
    uploadStatus.classList.remove('alert-info');
    uploadStatus.classList.add('alert-danger');

    // Activar progress bar de error con iconos
    updateUploadProgress(100, message, 'bi bi-exclamation-triangle-fill text-danger', true);

    // Re-habilitar botón
    const submitButton = document.getElementById('submitDocumentUpload');
    if (submitButton) {
        submitButton.disabled = false;
        submitButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5"/>
                <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708z"/>
            </svg>
            Upload
        `;
    }
}


function showUploadError(message) {
    const uploadStatus = document.getElementById('uploadStatus');
    const statusText = document.getElementById('uploadStatusText');
    const statusIcon = document.getElementById('uploadStatusIcon');

    uploadStatus.classList.remove('alert-info');
    uploadStatus.classList.add('alert-danger');

    if (statusText) statusText.textContent = message;
    if (statusIcon) statusIcon.className = 'bi bi-exclamation-triangle-fill text-danger';

    showToast(message, 'error');

    // Re-enable submit button
    const submitButton = document.getElementById('submitDocumentUpload');
    if (submitButton) {
        submitButton.disabled = false;
        submitButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5"/>
                <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708z"/>
            </svg>
            Upload
        `;
    }
}

function resetUploadForm() {
    if (documentPond) {
        documentPond.removeFiles();
    }

    resetDocumentTypeSelector();

    const uploadStatus = document.getElementById('uploadStatus');
    if (uploadStatus) {
        uploadStatus.classList.add('d-none');
        uploadStatus.classList.remove('alert-success', 'alert-danger', 'alert-info');
    }

    const submitButton = document.getElementById('submitDocumentUpload');
    if (submitButton) {
        submitButton.disabled = false;
        submitButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5"/>
                <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708z"/>
            </svg>
            Upload
        `;
    }
}

// Toast notification system
function showToast(message, type = 'info') {
    let toastContainer = document.getElementById('toastContainer');

    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast fade-in border-0 shadow-lg';
    toast.setAttribute('role', 'alert');

    let bgClass = 'bg-info';
    let textClass = 'text-white';
    let icon = '<i class="bi bi-info-circle-fill"></i>';

    if (type === 'success') {
        bgClass = 'bg-success';
        icon = '<i class="bi bi-check-circle-fill"></i>';
    } else if (type === 'error' || type === 'danger') {
        bgClass = 'bg-danger';
        icon = '<i class="bi bi-exclamation-triangle-fill"></i>';
    } else if (type === 'warning') {
        bgClass = 'bg-warning';
        textClass = 'text-dark';
        icon = '<i class="bi bi-exclamation-circle-fill"></i>';
    }

    toast.classList.add(bgClass, textClass);

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <div class="d-flex align-items-center">
                    <div class="me-2">${icon}</div>
                    <div>${message}</div>
                </div>
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.closest('.toast').remove()"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 3000);
}

// Utility function
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}