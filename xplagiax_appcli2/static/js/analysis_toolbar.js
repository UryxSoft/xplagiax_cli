// Obtener referencias a los elementos
const textArea = document.getElementById('main-textarea');
const alignLeftBtn = document.getElementById('alignLeft');
const alignCenterBtn = document.getElementById('alignCenter');
const alignRightBtn = document.getElementById('alignRight');
const allBtns = [alignLeftBtn, alignCenterBtn, alignRightBtn];

// Función para remover la clase 'active' de todos los botones
function removeActiveClass() {
    allBtns.forEach(btn => btn.classList.remove('active'));
}

// Función para aplicar alineación
function applyAlignment(alignment) {
    // Remover todas las clases de alineación existentes
    textArea.classList.remove('text-left', 'text-center', 'text-right');
    
    // Aplicar la nueva clase de alineación
    textArea.classList.add(alignment);
    
    // Remover clase active de todos los botones
    removeActiveClass();
}

// Event listeners para cada botón
alignLeftBtn.addEventListener('click', function() {
    applyAlignment('text-left');
    this.classList.add('active');
});

alignCenterBtn.addEventListener('click', function() {
    applyAlignment('text-center');
    this.classList.add('active');
});

alignRightBtn.addEventListener('click', function() {
    applyAlignment('text-right');
    this.classList.add('active');
});

// Función alternativa usando un solo event listener (más eficiente)
function setupAlignmentButtons() {
    const alignments = {
        'alignLeft': 'text-left',
        'alignCenter': 'text-center',
        'alignRight': 'text-right'
    };

    // Event delegation para todos los botones de alineación
    document.querySelector('.toolbar-group').addEventListener('click', function(e) {
        const btn = e.target.closest('.toolbar-btn');
        if (!btn) return;

        const alignment = alignments[btn.id];
        if (alignment) {
            // Remover todas las clases de alineación
            textArea.classList.remove('text-left', 'text-center', 'text-right');
            
            // Aplicar nueva alineación
            textArea.classList.add(alignment);
            
            // Actualizar botón activo
            removeActiveClass();
            btn.classList.add('active');
        }
    });
}

// Función para obtener la alineación actual
function getCurrentAlignment() {
    if (textArea.classList.contains('text-left')) return 'left';
    if (textArea.classList.contains('text-center')) return 'center';
    if (textArea.classList.contains('text-right')) return 'right';
    return 'left'; // por defecto
}

// Función para establecer alineación programáticamente
function setAlignment(alignment) {
    const alignmentMap = {
        'left': 'text-left',
        'center': 'text-center',
        'right': 'text-right'
    };

    const buttonMap = {
        'left': alignLeftBtn,
        'center': alignCenterBtn,
        'right': alignRightBtn
    };

    const cssClass = alignmentMap[alignment];
    const button = buttonMap[alignment];

    if (cssClass && button) {
        textArea.classList.remove('text-left', 'text-center', 'text-right');
        textArea.classList.add(cssClass);
        removeActiveClass();
        button.classList.add('active');
    }
}

// Ejemplo de uso de las funciones auxiliares
console.log('Funciones disponibles:');
console.log('- getCurrentAlignment(): devuelve la alineación actual');
console.log('- setAlignment("left"|"center"|"right"): establece alineación programáticamente');

// Inicializar con alineación izquierda por defecto
setAlignment('left');