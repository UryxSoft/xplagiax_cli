const iconClasses = [
    "bi-file-earmark",     // archivo
    "bi-robot",            // robot
    "bi-image",            // imagen
    "bi-file-earmark-text",
    "bi-file-earmark-code"
  ];

  function applyFloatingIconsTo(divId) {
    const container = document.getElementById(divId);
    container.classList.add("float-container");

    function createIcon() {
      const icon = document.createElement("i");
      icon.className = `bi ${iconClasses[Math.floor(Math.random() * iconClasses.length)]} floating-icon`;

      const containerWidth = container.offsetWidth;
      const containerHeight = container.offsetHeight;

      const x = Math.random() * (containerWidth - 30);
      const y = Math.random() * (containerHeight - 30);

      icon.style.left = `${x}px`;
      icon.style.top = `${y}px`;

      const size = 12 + Math.random() * 8; // Tamaño entre 12 y 20 px
      icon.style.fontSize = `${size}px`;

      const duration = 4 + Math.random() * 3;
      icon.style.animationDuration = `${duration}s`;

      container.appendChild(icon);

      setTimeout(() => {
        icon.remove();
      }, duration * 1000);
    }

    // Este código reemplaza el setInterval
    setInterval(() => {
        createIcon();
        createIcon();
        createIcon();
        createIcon(); // Lanza 2 iconos a la vez (puedes duplicar más)
    }, 100); // Más frecuencia (menos milisegundos)

  }
applyFloatingIconsTo("myDiv");